#!/bin/bash

# Instagram API Test Script
# This script tests Instagram API connectivity and posting functionality
# with detailed debugging and validation procedures

set -e  # Exit on any error

# ============================================================================
# HARDCODED CREDENTIALS - UPDATE THESE WITH YOUR ACTUAL VALUES
# ============================================================================

# STEP 1: UPDATE THESE CREDENTIALS WITH YOUR ACTUAL VALUES
INSTAGRAM_ACCESS_TOKEN="INSTAGRAM_ACCESS_TOKEN"
INSTAGRAM_USER_ID="INSTAGRAM_USER_ID"
INSTAGRAM_APP_ID="INSTAGRAM_APP_ID"
INSTAGRAM_APP_SECRET="INSTAGRAM_APP_SECRET"
INSTAGRAM_USERNAME="@gemnar_"

# Test content for posting
TEST_CAPTION="🚀 Testing Instagram API integration! Posted Automatically by Gemnar #automated #testing $(date '+%Y-%m-%d %H:%M:%S')"
TEST_IMAGE_URL="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop&crop=center"  # Sample test image

# ============================================================================
# COLOR CODES FOR OUTPUT
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo -e "\n${PURPLE}============================================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}============================================================================${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}📋 STEP $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

check_dependencies() {
    print_step "1" "Checking Dependencies"
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    print_success "curl is available"
    
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. JSON responses will be less readable"
        echo "Install with: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
        USE_JQ=false
    else
        print_success "jq is available for JSON formatting"
        USE_JQ=true
    fi
}

format_json() {
    if [ "$USE_JQ" = true ]; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

validate_credentials() {
    print_step "2" "Validating Credentials"
    
    # Check if credentials are set
    if [ "$INSTAGRAM_ACCESS_TOKEN" = "YOUR_LONG_LIVED_ACCESS_TOKEN_HERE" ]; then
        print_error "INSTAGRAM_ACCESS_TOKEN not set"
        print_setup_instructions
        exit 1
    fi
    
    if [ "$INSTAGRAM_USER_ID" = "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID_HERE" ]; then
        print_error "INSTAGRAM_USER_ID not set"
        print_setup_instructions
        exit 1
    fi
    
    if [ "$INSTAGRAM_APP_ID" = "YOUR_FACEBOOK_APP_ID_HERE" ]; then
        print_error "INSTAGRAM_APP_ID not set"
        print_setup_instructions
        exit 1
    fi
    
    if [ "$INSTAGRAM_APP_SECRET" = "YOUR_FACEBOOK_APP_SECRET_HERE" ]; then
        print_error "INSTAGRAM_APP_SECRET not set"
        print_setup_instructions
        exit 1
    fi
    
    print_success "All credentials are set"
    
    # Print masked credentials for verification
    echo -e "\n${CYAN}Current Credentials (masked):${NC}"
    echo "  Access Token: ${INSTAGRAM_ACCESS_TOKEN:0:10}...${INSTAGRAM_ACCESS_TOKEN: -10}"
    echo "  User ID: $INSTAGRAM_USER_ID"
    echo "  App ID: $INSTAGRAM_APP_ID"
    echo "  App Secret: ${INSTAGRAM_APP_SECRET:0:5}...${INSTAGRAM_APP_SECRET: -5}"
    echo "  Username: $INSTAGRAM_USERNAME"
}

debug_access_token() {
    print_step "3" "Testing Access Token with Instagram API"
    
    print_info "Testing access token validity with Instagram Graph API..."
    
    # Test Instagram API directly instead of Facebook debug API
    test_url="https://graph.instagram.com/v18.0/me"
    test_response=$(curl -s -G "$test_url" \
        -d "fields=id,username,account_type,media_count" \
        -d "access_token=$INSTAGRAM_ACCESS_TOKEN")
    
    echo -e "\n${CYAN}Instagram API Test Response:${NC}"
    format_json "$test_response"
    
    # Check if token is valid
    if echo "$test_response" | grep -q '"id"'; then
        print_success "Access token is valid and has Instagram permissions"
        
        # Extract user info
        if [ "$USE_JQ" = true ]; then
            user_id=$(echo "$test_response" | jq -r '.id // "Unknown"')
            username=$(echo "$test_response" | jq -r '.username // "Unknown"')
            account_type=$(echo "$test_response" | jq -r '.account_type // "Unknown"')
            media_count=$(echo "$test_response" | jq -r '.media_count // "Unknown"')
            
            echo -e "\n${CYAN}Token Details:${NC}"
            echo "  Instagram User ID: $user_id"
            echo "  Username: @$username"
            echo "  Account Type: $account_type"
            echo "  Media Count: $media_count"
            
            # Check if this matches our configured User ID
            if [ "$user_id" = "$INSTAGRAM_USER_ID" ]; then
                print_success "User ID matches configured INSTAGRAM_USER_ID"
            else
                print_warning "User ID mismatch: Token is for $user_id, but script configured for $INSTAGRAM_USER_ID"
                print_info "Consider updating INSTAGRAM_USER_ID to: $user_id"
            fi
            
            # Check account type
            if [ "$account_type" = "BUSINESS" ] || [ "$account_type" = "CREATOR" ]; then
                print_success "Account type ($account_type) supports content publishing"
            else
                print_warning "Account type ($account_type) may not support all Instagram API features"
            fi
        fi
    else
        print_error "Access token is invalid or doesn't have Instagram permissions"
        
        # Check for common errors
        if echo "$test_response" | grep -q "Invalid OAuth access token"; then
            print_error "Token is invalid or expired"
        elif echo "$test_response" | grep -q "Insufficient permissions"; then
            print_error "Token doesn't have required Instagram permissions"
            print_info "Make sure your token includes: instagram_basic, instagram_content_publish"
        elif echo "$test_response" | grep -q '"error"'; then
            error_message=$(echo "$test_response" | jq -r '.error.message // "Unknown error"' 2>/dev/null || echo "Unknown error")
            print_error "API Error: $error_message"
        fi
        return 1
    fi
}

test_instagram_account() {
    print_step "4" "Testing Instagram Business Account Access"
    
    # Test Instagram Business Account endpoint using Instagram Graph API
    account_url="https://graph.instagram.com/v18.0/$INSTAGRAM_USER_ID"
    account_response=$(curl -s -G "$account_url" \
        -d "fields=id,username,followers_count,follows_count,media_count,name,profile_picture_url,account_type" \
        -d "access_token=$INSTAGRAM_ACCESS_TOKEN")
    
    echo -e "\n${CYAN}Instagram Account Response:${NC}"
    format_json "$account_response"
    
    if echo "$account_response" | grep -q '"error"'; then
        print_error "Failed to access Instagram Business Account"
        
        # Check for common errors
        if echo "$account_response" | grep -q "Tried accessing nonexisting field"; then
            print_error "The User ID appears to be invalid"
        elif echo "$account_response" | grep -q "Invalid user id"; then
            print_error "Invalid Instagram User ID"
        elif echo "$account_response" | grep -q "Invalid OAuth access token"; then
            print_error "Invalid or expired access token"
        fi
        return 1
    else
        print_success "Successfully accessed Instagram Business Account"
        
        if [ "$USE_JQ" = true ]; then
            username=$(echo "$account_response" | jq -r '.username // "Unknown"')
            followers=$(echo "$account_response" | jq -r '.followers_count // "Unknown"')
            following=$(echo "$account_response" | jq -r '.follows_count // "Unknown"')
            media_count=$(echo "$account_response" | jq -r '.media_count // "Unknown"')
            account_type=$(echo "$account_response" | jq -r '.account_type // "Unknown"')
            
            echo -e "\n${CYAN}Account Details:${NC}"
            echo "  Username: @$username"
            echo "  Account Type: $account_type"
            echo "  Followers: $followers"
            echo "  Following: $following"
            echo "  Posts: $media_count"
            
            if [ "$INSTAGRAM_USERNAME" != "@$username" ]; then
                print_warning "Username mismatch: Expected $INSTAGRAM_USERNAME, got @$username"
            fi
        fi
    fi
}

test_media_permissions() {
    print_step "5" "Testing Media Upload Permissions"
    
    # Test media endpoint access using Instagram Graph API
    media_url="https://graph.instagram.com/v18.0/$INSTAGRAM_USER_ID/media"
    media_response=$(curl -s -G "$media_url" \
        -d "fields=id,caption,media_type,permalink,timestamp" \
        -d "limit=1" \
        -d "access_token=$INSTAGRAM_ACCESS_TOKEN")
    
    echo -e "\n${CYAN}Media Access Response:${NC}"
    format_json "$media_response"
    
    if echo "$media_response" | grep -q '"error"'; then
        print_error "Cannot access media endpoint"
        
        if echo "$media_response" | grep -q "Insufficient permissions"; then
            print_error "Missing instagram_content_publish permission"
            print_info "Make sure your app has the instagram_content_publish scope approved"
        fi
        return 1
    else
        print_success "Media endpoint accessible"
        
        if [ "$USE_JQ" = true ]; then
            media_count=$(echo "$media_response" | jq -r '.data | length')
            if [ "$media_count" -gt 0 ]; then
                print_success "Found $media_count existing media item(s)"
            else
                print_info "No existing media found (account may be new)"
            fi
        fi
    fi
}

create_test_post() {
    print_step "6" "Creating Test Instagram Post"
    
    print_info "Creating media container..."
    
    # Create media container using Instagram Graph API
    container_url="https://graph.instagram.com/v18.0/$INSTAGRAM_USER_ID/media"
    container_response=$(curl -s -X POST "$container_url" \
        -d "image_url=$TEST_IMAGE_URL" \
        -d "caption=$TEST_CAPTION" \
        -d "access_token=$INSTAGRAM_ACCESS_TOKEN")
    
    echo -e "\n${CYAN}Media Container Response:${NC}"
    format_json "$container_response"
    
    if echo "$container_response" | grep -q '"error"'; then
        print_error "Failed to create media container"
        
        if echo "$container_response" | grep -q "Invalid image URL"; then
            print_error "Image URL is invalid or inaccessible"
        elif echo "$container_response" | grep -q "Insufficient permissions"; then
            print_error "Missing content publishing permissions"
        elif echo "$container_response" | grep -q "User media creation disabled"; then
            print_error "Media creation is disabled for this account"
        fi
        return 1
    fi
    
    if [ "$USE_JQ" = true ]; then
        creation_id=$(echo "$container_response" | jq -r '.id // ""')
        
        if [ -n "$creation_id" ] && [ "$creation_id" != "null" ]; then
            print_success "Media container created with ID: $creation_id"
            
            print_info "Waiting 2 seconds for container to be ready..."
            sleep 2
            
            print_info "Publishing media container..."
            
            # Publish the media using Instagram Graph API
            publish_url="https://graph.instagram.com/v18.0/$INSTAGRAM_USER_ID/media_publish"
            publish_response=$(curl -s -X POST "$publish_url" \
                -d "creation_id=$creation_id" \
                -d "access_token=$INSTAGRAM_ACCESS_TOKEN")
            
            echo -e "\n${CYAN}Publish Response:${NC}"
            format_json "$publish_response"
            
            if echo "$publish_response" | grep -q '"error"'; then
                print_error "Failed to publish media"
                error_message=$(echo "$publish_response" | jq -r '.error.message // "Unknown error"' 2>/dev/null || echo "Unknown error")
                print_error "Error: $error_message"
                return 1
            else
                post_id=$(echo "$publish_response" | jq -r '.id // ""')
                print_success "✨ Post published successfully!"
                print_success "Instagram Post ID: $post_id"
                print_success "Check your Instagram account $INSTAGRAM_USERNAME for the new post!"
                
                # Generate Instagram URL (approximate)
                echo -e "\n${GREEN}🎉 SUCCESS! Your Instagram API integration is working correctly!${NC}"
                echo -e "${GREEN}You can now use this setup for automated Instagram posting in your application!${NC}"
            fi
        else
            print_error "Failed to get creation ID from container response"
            return 1
        fi
    else
        print_warning "Cannot extract creation ID without jq. Install jq for full testing."
        return 1
    fi
}

print_setup_instructions() {
    print_header "INSTAGRAM API SETUP INSTRUCTIONS"
    
    echo -e "${YELLOW}If this script failed, follow these steps to set up Instagram API correctly:${NC}\n"
    
    echo -e "${CYAN}1. CREATE FACEBOOK APP${NC}"
    echo "   • Go to https://developers.facebook.com/apps/"
    echo "   • Create a new app (Business type)"
    echo "   • Note your App ID and App Secret"
    
    echo -e "\n${CYAN}2. ADD INSTAGRAM PRODUCT${NC}"
    echo "   • In your app dashboard, add the Instagram product"
    echo "   • Choose 'API setup with Instagram login'"
    
    echo -e "\n${CYAN}3. CONNECT INSTAGRAM BUSINESS ACCOUNT${NC}"
    echo "   • Your Instagram account must be a Business or Creator account"
    echo "   • It must be linked to a Facebook Page"
    echo "   • Add your Instagram account as a test user in App Roles"
    
    echo -e "\n${CYAN}4. GET ACCESS TOKEN${NC}"
    echo "   • Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/"
    echo "   • Select your app"
    echo "   • Get User Access Token with these permissions:"
    echo "     - instagram_basic"
    echo "     - instagram_content_publish"
    echo "     - pages_show_list"
    echo "   • Exchange for long-lived token (60 days)"
    
    echo -e "\n${CYAN}5. GET INSTAGRAM BUSINESS ACCOUNT ID${NC}"
    echo "   • Use Graph API Explorer to call: me/accounts"
    echo "   • Look for 'instagram_business_account' in the response"
    echo "   • Use that ID, NOT your Facebook User ID"
    
    echo -e "\n${CYAN}6. UPDATE SCRIPT CREDENTIALS${NC}"
    echo "   • Edit this script and replace the placeholder values:"
    echo "   • INSTAGRAM_ACCESS_TOKEN: Your long-lived access token"
    echo "   • INSTAGRAM_USER_ID: Your Instagram Business Account ID"
    echo "   • INSTAGRAM_APP_ID: Your Facebook App ID"
    echo "   • INSTAGRAM_APP_SECRET: Your Facebook App Secret"
    echo "   • INSTAGRAM_USERNAME: Your Instagram username"
    
    echo -e "\n${CYAN}7. COMMON ISSUES${NC}"
    echo "   • Error 100: Using Facebook User ID instead of Instagram Business Account ID"
    echo "   • Error 190: Invalid/expired access token"
    echo "   • Error 10: Missing permissions or app not approved"
    echo "   • Make sure your app is in Live mode for production posting"
    
    echo -e "\n${CYAN}8. HELPFUL LINKS${NC}"
    echo "   • App Dashboard: https://developers.facebook.com/apps/$INSTAGRAM_APP_ID/"
    echo "   • Token Debugger: https://developers.facebook.com/tools/debug/accesstoken/"
    echo "   • Graph API Explorer: https://developers.facebook.com/tools/explorer/"
    echo "   • Instagram API Docs: https://developers.facebook.com/docs/instagram-api/"
}

run_tests() {
    print_header "INSTAGRAM API TEST SUITE"
    
    check_dependencies
    validate_credentials
    
    if debug_access_token && test_instagram_account && test_media_permissions; then
        echo -e "\n${GREEN}🎯 All validation tests passed! Creating test post automatically...${NC}"
        
        echo -e "\n${CYAN}📝 Post Details:${NC}"
        echo -e "${CYAN}Caption: $TEST_CAPTION${NC}"
        echo -e "${CYAN}Image: $TEST_IMAGE_URL${NC}"
        
        create_test_post
    else
        print_error "Some tests failed. Please check the setup instructions above."
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Check if running with --help or -h
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    print_setup_instructions
    exit 0
fi

# Run the test suite
run_tests

echo -e "\n${PURPLE}============================================================================${NC}"
echo -e "${PURPLE}Instagram API Test Complete${NC}"
echo -e "${PURPLE}============================================================================${NC}\n" 