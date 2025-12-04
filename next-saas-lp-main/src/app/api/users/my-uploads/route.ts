import { NextRequest, NextResponse } from 'next/server';

// Mock uploads data for Instagram gallery
const mockUploads = [
  {
    id: 1,
    image_url: 'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=400&h=400&fit=crop',
    public_id: 'sample_1',
    created_at: '2024-12-01T10:00:00Z',
  },
  {
    id: 2,
    image_url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=400&fit=crop',
    public_id: 'sample_2', 
    created_at: '2024-12-01T09:00:00Z',
  },
  {
    id: 3,
    image_url: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=400&fit=crop',
    public_id: 'sample_3',
    created_at: '2024-11-30T15:00:00Z',
  },
  {
    id: 4,
    image_url: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=400&h=400&fit=crop',
    public_id: 'sample_4',
    created_at: '2024-11-30T12:00:00Z',
  },
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format');
    
    // First try to proxy to Django
    const token = request.headers.get('Authorization');
    if (token) {
      try {
        const djangoUrl = `http://127.0.0.1:8000/api/users/my-uploads/?format=${format || 'instagram'}`;
        const response = await fetch(djangoUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token,
          },
          signal: AbortSignal.timeout(2000)
        });
        
        if (response.ok) {
          const data = await response.json();
          return NextResponse.json(data);
        }
      } catch (error) {
        console.warn('Django API not available, using mock data:', error);
      }
    }
    
    // Fallback to mock data
    if (format === 'instagram') {
      return NextResponse.json(mockUploads);
    }
    
    // Detailed format fallback
    return NextResponse.json({
      success: true,
      local_uploads: [],
      cloudinary_uploads: mockUploads.map(upload => ({
        id: upload.id,
        public_id: upload.public_id,
        url: upload.image_url,
        thumbnail_url: upload.image_url,
        original_filename: `image_${upload.id}.jpg`,
        format: 'jpg',
        width: 400,
        height: 400,
        file_size: 50000,
        purpose: 'instagram',
        usage_count: 1,
        created_at: upload.created_at,
        storage_type: 'cloudinary',
      })),
      total_local: 0,
      total_cloudinary: mockUploads.length,
      quota: null,
    });
    
  } catch (error) {
    console.error('Error in uploads API:', error);
    return NextResponse.json({ error: 'Failed to fetch uploads' }, { status: 500 });
  }
}