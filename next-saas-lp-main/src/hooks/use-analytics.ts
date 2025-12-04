// Mock analytics hook
export function useAnalytics() {
  return {
    track: (category: string, action: string, label: string, props?: any) => {
      // Mock analytics - could integrate with your Django analytics
      console.log('Analytics:', { category, action, label, props });
    },
  };
}
