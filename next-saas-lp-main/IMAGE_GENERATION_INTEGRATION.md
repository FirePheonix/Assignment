# Image Generation Integration - Complete Implementation

## ✅ What Was Implemented

### Backend (Django) - 6 New Advanced Endpoints

#### 1. **Multi-Reference Image Generation**
- **Endpoint**: `/api/ai/gpt-image/multi-reference/`
- **Use Case**: Upload 2+ reference images to generate a composite
- **Example**: Combine product photos into a gift basket scene
- **Parameters**: Multiple `image_0`, `image_1`, etc. files + prompt

#### 2. **Image Inpainting (Edit with Mask)**
- **Endpoint**: `/api/ai/gpt-image/inpainting/`
- **Use Case**: Edit specific parts of an image using a mask
- **Example**: Replace background, change object colors, add/remove elements
- **Parameters**: `image`, `mask` (with alpha channel), `prompt`

#### 3. **High Input Fidelity Editing**
- **Endpoint**: `/api/ai/gpt-image/high-fidelity/`
- **Use Case**: Preserve faces, logos, and fine details when editing
- **Example**: Add logo to clothing while preserving facial details
- **Parameters**: Multiple images + `prompt`, `input_fidelity=high`

#### 4. **Advanced Generation with All Options**
- **Endpoint**: `/api/ai/gpt-image/advanced/`
- **Use Case**: Full control over generation parameters
- **Parameters**: 
  - `size`: auto, 1024x1024, 1536x1024, 1024x1536
  - `quality`: auto, low, medium, high
  - `background`: auto, transparent, opaque
  - `output_format`: png, jpeg, webp
  - `output_compression`: 0-100
  - `moderation`: auto, low
  - `n`: 1-10 images at once

#### 5. **Transparent Background Generation**
- **Endpoint**: `/api/ai/gpt-image/transparent/`
- **Use Case**: Generate sprites, logos, stickers, design elements
- **Example**: Create a transparent PNG sprite sheet
- **Parameters**: `prompt`, `size`, `quality` (works best with medium/high)

#### 6. **Streaming Image Generation**
- **Endpoint**: `/api/ai/gpt-image/stream/`
- **Use Case**: Real-time progressive image updates (SSE)
- **Example**: Show 0-3 partial images as generation progresses
- **Parameters**: `prompt`, `size`, `quality`, `partial_images` (0-3)

---

### Frontend (Next.js) - Smart API Integration

#### New API Service: `/src/lib/api/image-generation.ts`

**Key Features:**
- ✅ **Intelligent Endpoint Selection**: Automatically chooses the right backend endpoint based on:
  - Number of reference images (1 vs multiple)
  - Presence of mask (inpainting)
  - Input fidelity requirements
  - Transparent background needs

- ✅ **Base64 to Data URL Conversion**: All images returned as ready-to-use data URLs

- ✅ **File Upload Handling**: Converts blob URLs to File objects for API upload

- ✅ **Error Handling**: Comprehensive try-catch with detailed logging

**Functions:**
```typescript
generateImage(params)          // Text-to-image generation
editImageWithReferences(params) // Smart editing with auto-endpoint selection
generateTransparentImage(params) // Transparent backgrounds
streamImageGeneration(params)   // Streaming with callbacks
```

#### Updated Server Actions: `/src/app/actions/ai.ts`

**`generateImageAction`**:
- Connects to Django `/api/ai/gpt-image/advanced/`
- Combines instructions + prompt
- Returns base64 data URL

**`editImageAction`**:
- Automatically detects number of reference images
- Selects appropriate endpoint:
  - 1 image → `/api/ai/edit-image-openai/`
  - Multiple images → `/api/ai/gpt-image/multi-reference/`
  - With mask → `/api/ai/gpt-image/inpainting/`
  - High fidelity → `/api/ai/gpt-image/high-fidelity/`
- Preserves all reference images in the request

---

## 🔄 How the Flow Works

### Scenario 1: Simple Text-to-Image
```
User types prompt → Text Node → Image Node (Transform)
                                     ↓
                            generateImageAction
                                     ↓
                          /api/ai/gpt-image/advanced/
                                     ↓
                         Returns base64 data URL
                                     ↓
                         Displayed in Image Node
```

### Scenario 2: Image Reference Generation
```
User uploads image → Image Node (Primitive) → Image Node (Transform)
User connects Text Node with prompt    ↗
                                     ↓
                            editImageAction
                                     ↓
               Detects: 1 uploaded + 0 incoming = single edit
                                     ↓
                      /api/ai/edit-image-openai/
                                     ↓
                         Returns edited image
```

### Scenario 3: Multiple Reference Images (Gift Basket)
```
Image Node 1 (product 1) ↘
Image Node 2 (product 2) → Image Node (Transform) + Text prompt
Image Node 3 (product 3) ↗
                                     ↓
                            editImageAction
                                     ↓
        Detects: 3 reference images → multi-reference endpoint
                                     ↓
              /api/ai/gpt-image/multi-reference/
                                     ↓
              Generates composite with all 3 products
```

### Scenario 4: High Fidelity Logo Addition
```
Image Node (woman photo) ↘
Image Node (logo)        → Image Node (Transform) + "Add logo to shirt"
                                     ↓
                            editImageAction
                                     ↓
        Detects: 2 images + high fidelity model
                                     ↓
              /api/ai/gpt-image/high-fidelity/
                                     ↓
        Logo added while preserving facial details
```

---

## 🎨 Image Node Intelligence

The Image Node automatically:

1. **Collects all inputs**:
   - Uploaded image (if any)
   - Incoming image nodes
   - Text nodes for prompts
   - Instructions field

2. **Displays reference preview**:
   ```
   📸 Reference Images (3)
   [img1] [img2] [img3]
   ```

3. **Builds combined prompt**:
   - Instructions field
   - All text node outputs
   - Joined with `\n\n`

4. **Selects generation mode**:
   - No refs → `generateImageAction` → Text-to-image
   - Has refs → `editImageAction` → Multi-reference/editing

5. **Shows generated result**:
   - Base64 data URL displayed as `<Image>`
   - Download button enabled
   - Regenerate option available

---

## 🔧 Environment Setup

### Django Backend
```bash
# .env
OPENAI_API_KEY=sk-...
RUNWARE_API_KEY=...  # Optional, for Runware endpoints
```

### Next.js Frontend
```bash
# .env.local
NEXT_PUBLIC_DJANGO_URL=http://localhost:8000
```

---

## 🚀 Testing the Integration

### Test 1: Basic Text-to-Image
1. Add Image Node (Transform)
2. Add Text Node with prompt: "A cute cat wearing a hat"
3. Connect Text → Image
4. Press Play ▶️ on Image Node
5. Should generate image and display it

### Test 2: Single Image Edit
1. Add Image Node (Primitive)
2. Upload a photo
3. Add Image Node (Transform)
4. Connect uploaded Image → Transform Image
5. Add instructions: "Make it look like a painting"
6. Press Play ▶️
7. Should edit the image

### Test 3: Multiple Reference Images
1. Add 3 Image Nodes (Primitive)
2. Upload 3 different product images
3. Add Image Node (Transform)
4. Connect all 3 images → Transform Image
5. Add Text Node: "Create a gift basket containing all these items"
6. Connect Text → Transform Image
7. Press Play ▶️
8. Should generate composite image

### Test 4: Transparent Background
1. Modify Image Node to use transparent endpoint
2. Prompt: "A pixel art sprite of a cat"
3. Should generate PNG with transparent background

---

## 📝 API Request Examples

### Single Image Generation
```bash
curl -X POST http://localhost:8000/api/ai/gpt-image/advanced/ \
  -H "Cookie: sessionid=..." \
  -F "prompt=A futuristic cityscape at sunset" \
  -F "size=1024x1024" \
  -F "quality=high"
```

### Multi-Reference Generation
```bash
curl -X POST http://localhost:8000/api/ai/gpt-image/multi-reference/ \
  -H "Cookie: sessionid=..." \
  -F "prompt=Combine all these into a gift basket" \
  -F "image_0=@product1.jpg" \
  -F "image_1=@product2.jpg" \
  -F "image_2=@product3.jpg" \
  -F "quality=high"
```

### Inpainting with Mask
```bash
curl -X POST http://localhost:8000/api/ai/gpt-image/inpainting/ \
  -H "Cookie: sessionid=..." \
  -F "prompt=Add a flamingo to the pool" \
  -F "image=@lounge.png" \
  -F "mask=@mask.png" \
  -F "quality=high"
```

---

## 🎯 Next Steps

1. **Test Each Endpoint**: Verify all 6 endpoints work with Postman/curl
2. **Start Django Server**: `poetry run python manage.py runserver`
3. **Start Next.js**: `npm run dev`
4. **Create Flow**: Test in Flow Generator page
5. **Monitor Logs**: Check console for detailed logging at each step

---

## 🐛 Debugging

### Backend logs show:
- `🎨 IMAGE NODE GENERATING:` - Full node context
- Request details: prompts, images, model, size
- Endpoint selection logic

### Frontend logs show:
- `🎨 Using endpoint:` - Which API endpoint was chosen
- Image count, mask presence, fidelity mode
- Response data with base64 length

### Common Issues:

1. **"No image returned"**: Check OpenAI API key in Django
2. **CORS errors**: Ensure `credentials: 'include'` in fetch
3. **Auth errors**: Make sure user is logged in to Django
4. **File upload fails**: Check temp file permissions and multipart parser

---

## 💡 Key Innovations

1. **Smart Endpoint Selection**: Frontend automatically picks the right backend endpoint
2. **Unified Interface**: One `editImageAction` handles all scenarios
3. **Base64 Data URLs**: No file storage needed, instant preview
4. **Reference Image Preservation**: All connected images used, not just first one
5. **Visual Feedback**: Shows reference count and types in UI
6. **Comprehensive Logging**: Easy to debug with detailed console logs
