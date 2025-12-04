import { NextRequest, NextResponse } from 'next/server';

// Mock brands data
const mockBrands = [
  {
    id: 1,
    name: 'gemnarr',
    slug: 'gemnarr',
    has_twitter_config: true,
    has_instagram_config: false,
    description: 'Main brand for Gemnar'
  },
  {
    id: 2,
    name: 'nn',
    slug: 'nn',
    has_twitter_config: false,
    has_instagram_config: false,
    description: 'Secondary brand'
  }
];

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params;
    
    // First try to proxy to Django
    const djangoUrl = `http://127.0.0.1:8000/api/brands/${slug}/`;
    
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
      console.warn(`Django API not available for brand ${slug}, using mock data:`, error);
    }
    
    // Fallback to mock data
    const brand = mockBrands.find(b => b.slug === slug) || {
      id: 1,
      name: slug,
      slug: slug,
      has_twitter_config: false,
      has_instagram_config: false,
      description: `Mock brand for ${slug}`
    };
    
    return NextResponse.json(brand);
  } catch (error) {
    console.error('Error in brand API:', error);
    
    // Always return mock data as final fallback
    return NextResponse.json({
      id: 1,
      name: 'unknown',
      slug: 'unknown',
      has_twitter_config: false,
      has_instagram_config: false,
      description: 'Mock brand'
    });
  }
}