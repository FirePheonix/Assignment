import { NextRequest, NextResponse } from 'next/server';

// Mock brands data (only brands for current user)
const mockBrands = [
  {
    id: 4,
    name: 'gemnarr',
    slug: 'gemnarr',
    has_twitter_config: true,
    has_instagram_config: false,
    description: 'Main brand for Gemnar'
  }
];

export async function GET(request: NextRequest) {
  try {
    // First try to proxy to Django
    const djangoUrl = 'http://127.0.0.1:8000/api/brands/';
    
    try {
      const response = await fetch(djangoUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': request.headers.get('Authorization') || '',
        },
        // Add a timeout to fail fast if Django is not responding
        signal: AbortSignal.timeout(3000)
      });
      
      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (error) {
      console.warn('Django API not available, using mock data:', error);
    }
    
    // Fallback to mock data
    return NextResponse.json(mockBrands);
  } catch (error) {
    console.error('Error in brands API:', error);
    // Always return mock data as final fallback
    return NextResponse.json(mockBrands);
  }
}