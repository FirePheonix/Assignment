import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/flow-components/ui/dialog';
import { handleError } from '@/lib/error/handle';
import { getCurrentUser } from '@/lib/auth';
import { uploadFile } from '@/lib/upload';
import { Loader2Icon } from 'lucide-react';
import Image from 'next/image';
import { type FormEventHandler, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Input } from './ui/input';
import {
  Dropzone,
  DropzoneContent,
  DropzoneEmptyState,
} from './ui/kibo-ui/dropzone';
import { Label } from './ui/label';

type ProfileProps = {
  open: boolean;
  setOpen: (open: boolean) => void;
};

export const Profile = ({ open, setOpen }: ProfileProps) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [image, setImage] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [password, setPassword] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      const user = await getCurrentUser();

      if (!user) {
        return;
      }

      if (user.first_name) {
        setName(`${user.first_name} ${user.last_name || ''}`.trim());
      } else if (user.username) {
        setName(user.username);
      }

      if (user.email) {
        setEmail(user.email);
      }

      // TODO: Add avatar support when Django user model has avatar field
      // if (user.avatar) {
      //   setImage(user.avatar);
      // }
    };

    loadProfile();
  }, []);

  const handleUpdateUser: FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault();

    if (!name.trim() || !email.trim() || isUpdating) {
      return;
    }

    setIsUpdating(true);

    try {
      // TODO: Implement Django profile update API endpoint
      // For now, just show a message
      toast.info('Profile update feature coming soon');
      
      // Example of what the API call would look like:
      // const token = localStorage.getItem('auth_token');
      // const response = await fetch(`${process.env.NEXT_PUBLIC_DJANGO_URL}/api/auth/profile/`, {
      //   method: 'PATCH',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Token ${token}`,
      //   },
      //   body: JSON.stringify({
      //     first_name: name.split(' ')[0],
      //     last_name: name.split(' ').slice(1).join(' '),
      //     email,
      //     ...(password && { password }),
      //   }),
      // });
      
      setOpen(false);
    } catch (error) {
      handleError('Error updating profile', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDrop = async (files: File[]) => {
    if (isUpdating) {
      return;
    }

    try {
      if (!files.length) {
        throw new Error('No file selected');
      }

      setIsUpdating(true);

      // TODO: Implement Django avatar upload
      toast.info('Avatar upload feature coming soon');
      
      // Example implementation:
      // const { url } = await uploadFile(files[0], 'avatars');
      // const token = localStorage.getItem('auth_token');
      // const response = await fetch(`${process.env.NEXT_PUBLIC_DJANGO_URL}/api/auth/profile/`, {
      //   method: 'PATCH',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Token ${token}`,
      //   },
      //   body: JSON.stringify({ avatar: url }),
      // });
      
      // setImage(url);
    } catch (error) {
      handleError('Error updating avatar', error);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen} modal={false}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Profile</DialogTitle>
          <DialogDescription>
            Update your profile information.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-2">
          <Label htmlFor="avatar">Avatar</Label>
          <Dropzone
            maxSize={1024 * 1024 * 10}
            minSize={1024}
            maxFiles={1}
            multiple={false}
            accept={{ 'image/*': [] }}
            onDrop={handleDrop}
            src={image ? [new File([], image)] : []}
            onError={console.error}
            className="relative aspect-square h-36 w-auto"
          >
            <DropzoneEmptyState />
            <DropzoneContent>
              {image && (
                <Image
                  src={image}
                  alt="Image preview"
                  className="absolute top-0 left-0 h-full w-full object-cover"
                  unoptimized
                  width={100}
                  height={100}
                />
              )}
              {isUpdating && (
                <div className="absolute inset-0 z-10 flex items-center justify-center">
                  <Loader2Icon size={24} className="animate-spin" />
                </div>
              )}
            </DropzoneContent>
          </Dropzone>
        </div>
        <form
          onSubmit={handleUpdateUser}
          className="mt-2 grid gap-4"
          aria-disabled={isUpdating}
        >
          <div className="grid gap-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="Jane Doe"
              value={name}
              onChange={({ target }) => setName(target.value)}
              className="text-foreground"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              placeholder="jane@doe.com"
              value={email}
              type="email"
              onChange={({ target }) => setEmail(target.value)}
              className="text-foreground"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              placeholder="••••••••"
              value={password}
              type="password"
              onChange={({ target }) => setPassword(target.value)}
              className="text-foreground"
            />
          </div>
          <Button
            type="submit"
            disabled={isUpdating || !name.trim() || !email.trim()}
          >
            Update
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};
