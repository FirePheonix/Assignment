import { Avatar, AvatarFallback, AvatarImage } from "@/components/flow-components/ui/avatar";

interface UserAvatarProps {
  user?: {
    first_name?: string;
    last_name?: string;
    username?: string;
    email?: string;
    profile_picture?: string | null;
  } | null;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizeClasses = {
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-16 h-16 text-lg",
  xl: "w-24 h-24 text-2xl",
};

export function UserAvatar({ user, size = "md", className = "" }: UserAvatarProps) {
  const getInitials = () => {
    if (user?.first_name) {
      const firstInitial = user.first_name[0]?.toUpperCase() || '';
      const lastInitial = user.last_name?.[0]?.toUpperCase() || '';
      return firstInitial + lastInitial;
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <Avatar className={`${sizeClasses[size]} ${className}`}>
      {user?.profile_picture && (
        <AvatarImage src={user.profile_picture} alt={user.username || 'User'} />
      )}
      <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white font-bold">
        {getInitials()}
      </AvatarFallback>
    </Avatar>
  );
}
