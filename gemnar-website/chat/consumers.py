import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import ChatRoom, ChatConversation, Message
import asyncio
import os
import time
from django.utils import timezone
import datetime

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "chat_message")

            if message_type == "chat_message":
                await self.handle_chat_message(data)
            elif message_type == "delivery_confirmation":
                await self.handle_delivery_confirmation(data)
            elif message_type == "typing":
                await self.handle_typing(data)
            else:
                await self.send_error("Unknown message type")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def handle_delivery_confirmation(self, data):
        """Handle delivery confirmation and delete message from server."""
        message_id = data.get("message_id")

        if not message_id:
            await self.send_error("Message ID is required for delivery confirmation")
            return

        # Delete message from server after client confirms receipt
        await self.delete_message_from_server(message_id)

    async def handle_chat_message(self, data):
        """Handle incoming chat messages (plain text)."""
        message_content = data.get("message", "")

        if not message_content:
            await self.send_error("Message content is required")
            return

        # Save message to database (encryption handled in model)
        message = await self.save_message(message_content)

        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": message.id,
                    "message": message_content,
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "timestamp": message.timestamp.isoformat(),
                    "image_url": message.image.url if message.image else None,
                },
            )

    async def handle_typing(self, data):
        """Handle typing indicators."""
        is_typing = data.get("is_typing", False)

        # Send typing indicator to room group (excluding sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": self.user.id,
                "username": self.user.username,
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        """Send message to WebSocket (called by group_send)."""
        # Don't send message back to sender
        if event["user_id"] != self.user.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "chat_message",
                        "message_id": event["message_id"],
                        "message": event["message"],
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "timestamp": event["timestamp"],
                        "image_url": event.get("image_url"),
                    }
                )
            )

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator back to sender
        if event["user_id"] != self.user.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing_indicator",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "is_typing": event["is_typing"],
                    }
                )
            )

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )

    @database_sync_to_async
    def save_message(self, message_content):
        """Save message to database (encryption handled in model)."""
        try:
            # Get conversation or room
            conversation = None
            room = None

            try:
                # Try to get conversation first (new format)
                conversation = ChatConversation.objects.get(id=int(self.room_name))
            except (ChatConversation.DoesNotExist, ValueError):
                # Fall back to room (legacy format)
                try:
                    room = ChatRoom.objects.get(id=int(self.room_name))
                except ChatRoom.DoesNotExist:
                    return None

            # Create message (content will be encrypted in model save method)
            message = Message.objects.create(
                conversation=conversation,
                room=room,
                sender=self.user,
                content=message_content,
            )

            # Update conversation/room timestamp
            if conversation:
                conversation.save(update_fields=["updated_at"])
            elif room:
                room.save(update_fields=["updated_at"])

            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def delete_message_from_server(self, message_id):
        """Delete message from server after client confirms receipt."""
        try:
            message = Message.objects.get(id=message_id)
            message.delete()
            return True
        except Message.DoesNotExist:
            return False


class ConversationConsumer(AsyncWebsocketConsumer):
    """Enhanced WebSocket consumer for the new conversation-based chat system."""

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"conversation_{self.conversation_id}"
        self.user = self.scope["user"]

        print(
            f"🔌 Consumer connect attempt: user={self.user.id if self.user.is_authenticated else 'Anonymous'}, conversation={self.conversation_id}"
        )

        # Only allow authenticated users
        if not self.user.is_authenticated:
            print("❌ Consumer: Rejecting unauthenticated user")
            await self.close(code=4001)
            return

        # Check if user is part of this conversation
        if not await self.is_user_in_conversation():
            print(
                f"❌ Consumer: User {self.user.id} not part of conversation {self.conversation_id}"
            )
            await self.close(code=4002)
            return

        print(
            f"✅ Consumer: Adding user {self.user.id} to room group '{self.room_group_name}'"
        )
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"🎉 Consumer: WebSocket connection accepted for user {self.user.id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "chat_message")

            if message_type == "chat_message":
                await self.handle_chat_message(data)
            elif message_type == "delivery_confirmation":
                await self.handle_delivery_confirmation(data)
            elif message_type == "typing":
                await self.handle_typing(data)
            else:
                await self.send_error("Unknown message type")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def handle_delivery_confirmation(self, data):
        """Handle delivery confirmation and delete message from server."""
        message_id = data.get("message_id")

        if not message_id:
            await self.send_error("Message ID is required for delivery confirmation")
            return

        # Delete message from server after client confirms receipt
        await self.delete_conversation_message_from_server(message_id)

    async def handle_chat_message(self, data):
        """Handle incoming chat messages (plain text)."""
        message_content = data.get("message", "")

        if not message_content:
            await self.send_error("Message content is required")
            return

        # Save message to database (encryption handled in model)
        message = await self.save_conversation_message(message_content)

        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": message.id,
                    "message": message_content,
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "timestamp": message.timestamp.isoformat(),
                    "image_url": message.image.url if message.image else None,
                },
            )

    async def handle_typing(self, data):
        """Handle typing indicators."""
        is_typing = data.get("is_typing", False)

        # Send typing indicator to room group (excluding sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": self.user.id,
                "username": self.user.username,
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        """Send message to WebSocket (called by group_send)."""
        print(f"🔄 Consumer received chat_message event: {event}")
        print(f"🔍 Current user ID: {self.user.id}, Event user ID: {event['user_id']}")

        # Don't send message back to sender
        if event["user_id"] != self.user.id:
            message_data = {
                "type": "chat_message",
                "message_id": event["message_id"],
                "message": event["message"],
                "user_id": event["user_id"],
                "username": event["username"],
                "timestamp": event["timestamp"],
                "image_url": event.get("image_url"),
            }
            print(f"📤 Sending message to websocket client: {message_data}")
            await self.send(text_data=json.dumps(message_data))
        else:
            print(f"🚫 Skipping message - same user ID ({self.user.id})")

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator back to sender
        if event["user_id"] != self.user.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing_indicator",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "is_typing": event["is_typing"],
                    }
                )
            )

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )

    @database_sync_to_async
    def is_user_in_conversation(self):
        """Check if the current user is part of this conversation."""
        try:
            conversation = ChatConversation.objects.get(id=self.conversation_id)
            return (
                self.user == conversation.participant1
                or self.user == conversation.participant2
                or (conversation.brand and self.user == conversation.brand.owner)
            )
        except ChatConversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_conversation_message(self, message_content):
        """Save message to database (encryption handled in model)."""
        try:
            conversation = ChatConversation.objects.get(id=self.conversation_id)

            # Create message (content will be encrypted in model save method)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=message_content,
            )

            # Update conversation timestamp
            conversation.save(update_fields=["updated_at"])

            return message
        except Exception as e:
            print(f"Error saving conversation message: {e}")
            return None

    @database_sync_to_async
    def delete_conversation_message_from_server(self, message_id):
        """Delete message from server after client confirms receipt."""
        try:
            message = Message.objects.get(id=message_id)
            message.delete()
            return True
        except Message.DoesNotExist:
            return False


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """Global WebSocket consumer for user notifications (new conversations, etc.)."""

    async def connect(self):
        self.user = self.scope["user"]

        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create a unique group for this user
        self.user_group_name = f"user_{self.user.id}"

        # Join user group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "ping")

            if message_type == "ping":
                await self.send(
                    text_data=json.dumps(
                        {"type": "pong", "message": "Connection active"}
                    )
                )
            else:
                await self.send_error("Unknown message type")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def new_conversation(self, event):
        """Send new conversation notification to user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_conversation",
                    "conversation_id": event["conversation_id"],
                    "conversation_name": event["conversation_name"],
                    "other_user": event["other_user"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def conversation_updated(self, event):
        """Send conversation update notification to user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "conversation_updated",
                    "conversation_id": event["conversation_id"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )


class AdminLogsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for admin log streaming."""

    async def connect(self):
        self.user = self.scope["user"]
        self.log_source = "django"  # Default source
        self.process = None
        self.is_connected = False
        self.read_task = None  # Track the reading task
        self.read_lock = asyncio.Lock()  # Prevent multiple readers

        # Only allow admin users
        if not self.user.is_authenticated or not (
            self.user.is_staff or self.user.is_superuser
        ):
            await self.close(code=4001)
            return

        # Create a unique group for this admin user
        self.admin_group_name = f"admin_logs_{self.user.id}"

        # Join admin group
        await self.channel_layer.group_add(self.admin_group_name, self.channel_name)
        await self.accept()
        self.is_connected = True

        # Send initial connection message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Admin logs WebSocket connected",
                    "user": self.user.username,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        self.is_connected = False

        # Use aggressive cleanup
        await self.stop_all_processes()

        # Leave admin group
        if hasattr(self, "admin_group_name"):
            await self.channel_layer.group_discard(
                self.admin_group_name, self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "ping")

            if message_type == "ping":
                await self.send(
                    text_data=json.dumps(
                        {"type": "pong", "message": "Connection active"}
                    )
                )
            elif message_type == "start_logs":
                await self.handle_start_logs(data)
            elif message_type == "stop_logs":
                await self.handle_stop_logs()
            elif message_type == "switch_source":
                await self.handle_switch_source(data)
            else:
                await self.send_error("Unknown message type")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def handle_start_logs(self, data):
        """Start streaming logs from the specified source."""
        self.log_source = data.get("source", "django")

        # Stop any existing log process with more aggressive cleanup
        await self.stop_all_processes()

        # Small delay to ensure cleanup is complete
        await asyncio.sleep(0.5)

        # Start new log process
        await self.start_log_process()

    async def stop_all_processes(self):
        """Aggressively stop all running processes and tasks."""
        # Cancel any running read task first
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
            try:
                await asyncio.wait_for(self.read_task, timeout=2)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            except Exception:
                pass
            finally:
                self.read_task = None

        # Terminate and kill process if necessary
        if self.process:
            try:
                # First try terminate
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except asyncio.TimeoutError:
                try:
                    # Force kill if terminate didn't work
                    self.process.kill()
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                self.process = None

    async def handle_stop_logs(self):
        """Stop the current log process."""
        await self.stop_all_processes()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "logs_stopped",
                    "message": "Log streaming stopped",
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def handle_switch_source(self, data):
        """Switch to a different log source."""
        new_source = data.get("source", "django")
        if new_source != self.log_source:
            self.log_source = new_source
            await self.handle_start_logs({"source": new_source})

    async def start_log_process(self):
        """Start the log streaming process."""
        # Define log sources
        log_sources = {
            "django": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "django.log"),
            ],
            "errors": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "errors.log"),
            ],
            "requests": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "requests.log"),
            ],
            "uvicorn": ["journalctl", "-u", "uvicorn.service", "-f", "--no-pager"],
            "nginx": ["journalctl", "-u", "nginx.service", "-f", "--no-pager"],
            "nginx_access": ["tail", "-f", "/var/log/nginx/access.log"],
            "nginx_error": ["tail", "-f", "/var/log/nginx/error.log"],
            "system": ["journalctl", "-f", "--no-pager", "-n", "20"],
        }

        command = log_sources.get(self.log_source, log_sources["django"])

        # Send connection message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "log_connection",
                    "message": f"Connecting to {self.log_source} logs...",
                    "command": " ".join(command),
                    "user": os.getenv("USER", "unknown"),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

        # Check if it's a file-based log source
        if command[0] == "tail":
            log_file = command[2]  # tail -f /path/to/file

            # Check if file exists
            if not os.path.exists(log_file):
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "log_warning",
                            "message": f"Log file does not exist: {log_file}",
                            "timestamp": timezone.now().isoformat(),
                        }
                    )
                )
                # Create directory and empty file if it doesn't exist
                try:
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    with open(log_file, "a") as f:
                        f.write(f"# Log file created at {timezone.now()}\n")
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "log_message",
                                "message": f"Created empty log file: {log_file}",
                                "timestamp": timezone.now().isoformat(),
                            }
                        )
                    )
                except Exception as e:
                    await self.send_error(f"Failed to create log file: {str(e)}")
                    return

            # Check if file is readable
            if not os.access(log_file, os.R_OK):
                await self.send_error(f"Log file not readable: {log_file}")
                return

        try:
            # Start the subprocess
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "log_started",
                        "message": f"Log process started (PID: {self.process.pid})",
                        "timestamp": timezone.now().isoformat(),
                    }
                )
            )

            # Start reading logs in a separate task
            self.read_task = asyncio.create_task(self.read_logs())

        except Exception as e:
            await self.send_error(f"Failed to start log process: {str(e)}")

    async def read_logs(self):
        """Read logs from the subprocess and send them via WebSocket."""
        if not self.process:
            return

        # Use lock to prevent multiple readers
        async with self.read_lock:
            # Double-check process is still valid after acquiring lock
            if not self.process or self.process.returncode is not None:
                return
            line_count = 0
            last_heartbeat = time.time()
            start_time = time.time()
            log_line_sent = False
            warning_sent = False
            consecutive_errors = 0
            max_consecutive_errors = 10

            try:
                while self.is_connected and self.process:
                    # Check if WebSocket is still connected
                    if not self.is_connected:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "log_message",
                                    "message": "WebSocket disconnected, stopping log stream",
                                    "timestamp": timezone.now().isoformat(),
                                }
                            )
                        )
                        break

                    # Check if process is still running
                    if self.process.returncode is not None:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "log_message",
                                    "message": f"Log process ended with code {self.process.returncode}",
                                    "timestamp": timezone.now().isoformat(),
                                }
                            )
                        )
                        break

                    current_time = time.time()

                    # Read a line from the process with increased timeout
                    try:
                        line = await asyncio.wait_for(
                            self.process.stdout.readline(), timeout=5.0
                        )

                        if line:
                            # Handle both string and bytes
                            if isinstance(line, bytes):
                                clean_line = line.decode(
                                    "utf-8", errors="ignore"
                                ).strip()
                            else:
                                clean_line = line.strip()

                            if clean_line:
                                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                line_count += 1
                                log_line_sent = True
                                consecutive_errors = (
                                    0  # Reset error counter on successful read
                                )
                                log_entry = f"[{timestamp}] {clean_line}"

                                await self.send(
                                    text_data=json.dumps(
                                        {
                                            "type": "log_message",
                                            "message": log_entry,
                                            "line_count": line_count,
                                            "timestamp": timezone.now().isoformat(),
                                        }
                                    )
                                )
                                last_heartbeat = current_time
                        else:
                            # Empty line or EOF
                            if not line:  # EOF
                                await self.send(
                                    text_data=json.dumps(
                                        {
                                            "type": "log_message",
                                            "message": "End of log stream reached - waiting for new logs...",
                                            "timestamp": timezone.now().isoformat(),
                                        }
                                    )
                                )
                                # For tail -f, EOF usually means the file was empty
                                # Don't break immediately, give it time to get new data
                                await asyncio.sleep(2)
                                continue

                    except asyncio.TimeoutError:
                        # No data available within timeout, continue
                        pass
                    except asyncio.CancelledError:
                        # Task was cancelled, break cleanly
                        break
                    except Exception as e:
                        consecutive_errors += 1
                        error_msg = f"Read error #{consecutive_errors}: {str(e)}"

                        # Only send error if we're still connected
                        if self.is_connected:
                            await self.send(
                                text_data=json.dumps(
                                    {
                                        "type": "log_warning",
                                        "message": error_msg,
                                        "timestamp": timezone.now().isoformat(),
                                    }
                                )
                            )

                        # Stop if too many consecutive errors
                        if consecutive_errors >= max_consecutive_errors:
                            if self.is_connected:
                                await self.send_error(
                                    f"Too many consecutive errors ({consecutive_errors}), stopping stream"
                                )
                            break

                        # Brief pause before retrying
                        await asyncio.sleep(0.5)

                    # Send warning if no logs received
                    if (
                        not log_line_sent
                        and not warning_sent
                        and (current_time - start_time) > 10
                    ):
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "log_warning",
                                    "message": f"⚠️ No logs received after 10 seconds from {self.log_source}. This may be normal if there's no activity.",
                                    "timestamp": timezone.now().isoformat(),
                                }
                            )
                        )
                        warning_sent = True

                    # Send heartbeat less frequently to reduce noise
                    if current_time - last_heartbeat > 10:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "heartbeat",
                                    "timestamp": timezone.now().isoformat(),
                                }
                            )
                        )
                        last_heartbeat = current_time

                    # Increased line limit
                    if line_count > 10000:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "log_limit",
                                    "message": "Line limit reached (10,000), stopping stream to prevent memory issues",
                                    "timestamp": timezone.now().isoformat(),
                                }
                            )
                        )
                        break

                    # Small delay to prevent excessive CPU usage
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                # Task was cancelled, this is expected
                pass
            except Exception as e:
                if self.is_connected:
                    await self.send_error(f"Critical error in log reading: {str(e)}")
            finally:
                # Clean up process
                if self.process:
                    try:
                        self.process.terminate()
                        await asyncio.wait_for(self.process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        try:
                            self.process.kill()
                            await asyncio.wait_for(self.process.wait(), timeout=2)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    finally:
                        self.process = None

                # Send final message only if still connected
                if self.is_connected:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "logs_stopped",
                                "message": "Log streaming stopped",
                                "timestamp": timezone.now().isoformat(),
                            }
                        )
                    )

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )


class TweetQueueConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time tweet queue updates"""

    async def connect(self):
        # Get brand and organization from URL parameters
        self.organization_pk = self.scope["url_route"]["kwargs"]["organization_pk"]
        self.brand_pk = self.scope["url_route"]["kwargs"]["brand_pk"]
        self.user = self.scope["user"]

        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check if user has access to this brand
        has_access = await self.check_brand_access()
        if not has_access:
            await self.close()
            return

        # Join brand-specific group
        self.room_group_name = f"tweet_queue_{self.organization_pk}_{self.brand_pk}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send initial server time
        await self.send_server_time()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "")

            if message_type == "ping":
                await self.send_pong()
            elif message_type == "request_server_time":
                await self.send_server_time()
            else:
                await self.send_error("Unknown message type")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def send_pong(self):
        """Send pong response"""
        await self.send(
            text_data=json.dumps(
                {"type": "pong", "timestamp": timezone.now().isoformat()}
            )
        )

    async def send_server_time(self):
        """Send current server time in UTC"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "server_time",
                    "timestamp": timezone.now().isoformat(),
                    "utc_timestamp": timezone.now().timestamp(),
                }
            )
        )

    async def tweet_status_update(self, event):
        """Handle tweet status update messages"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "tweet_status_update",
                    "tweet_id": event["tweet_id"],
                    "status": event["status"],
                    "posted_at": event.get("posted_at"),
                    "tweet_url": event.get("tweet_url"),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def tweet_posted(self, event):
        """Handle tweet posted messages"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "tweet_posted",
                    "tweet_id": event["tweet_id"],
                    "posted_at": event["posted_at"],
                    "tweet_url": event.get("tweet_url"),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def tweet_failed(self, event):
        """Handle tweet failed messages"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "tweet_failed",
                    "tweet_id": event["tweet_id"],
                    "error_message": event.get("error_message", "Unknown error"),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def brand_connected(self, event):
        """Handle brand connection notifications"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "brand_connected",
                    "brand_id": event["brand_id"],
                    "platform": event["platform"],
                    "username": event["username"],
                    "message": event["message"],
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def brand_disconnected(self, event):
        """Handle brand disconnection notifications"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "brand_disconnected",
                    "brand_id": event["brand_id"],
                    "platform": event["platform"],
                    "message": event["message"],
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def analytics_update(self, event):
        """Handle analytics updates"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "analytics_update",
                    "data": event["data"],
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    @database_sync_to_async
    def check_brand_access(self):
        """Check if user has access to this brand"""
        try:
            from website.models import Brand
            from organizations.models import Organization

            organization = Organization.objects.get(pk=self.organization_pk)
            Brand.objects.get(pk=self.brand_pk, organization=organization)

            # Check if user is an admin of the organization
            org_user = organization.organization_users.filter(user=self.user).first()
            return org_user is not None and org_user.is_admin
        except Exception:
            return False
