# Google Maps Integration Setup Guide

## Overview
The TenzorX HealthNav application includes an interactive map feature that displays hospital locations, allowing users to visualize provider options geographically.

## API Key Configuration

### Local Development Setup

1. **Get your Google Maps API Key:**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Maps SDK for Web
     - Places API
     - Geocoding API

2. **Create an API Key:**
   - Go to **Credentials** → **Create Credentials** → **API Key**
   - Copy your API key

3. **Configure Local Environment:**
   - Copy `.env.example` to `.env.local`:
     ```bash
     cp .env.example .env.local
     ```
   - Add your API key:
     ```
     NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE
     ```

4. **Restrict API Key (Recommended for Security):**
   - In Google Cloud Console, edit your API key
   - Set restrictions:
     - **HTTP referrers (Web sites)**: Add your domain
     - **Application restrictions**: Select "Maps SDK for Web"

### Production Deployment (Vercel)

The API key has been configured in Vercel environment variables:

1. **Environment Variables Set:**
   - `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` available in:
     - Production
     - Preview
     - Development

2. **Automatic Redeploy:**
   - Changes to environment variables trigger automatic redeployment
   - Map feature is now available to all users

## Features Available with Google Maps API

### Hospital Map View
- **Interactive Map**: Pan, zoom, and explore hospital locations
- **Markers**: Color-coded by hospital tier (Premium, Mid-range, Budget)
- **Info Windows**: Click markers to see:
  - Hospital name and location
  - Rating and reviews count
  - NABH accreditation status
  - Estimated cost range
  - Specializations
  - Direction link to Google Maps
- **Bounds Auto-Fit**: Map automatically adjusts to show all hospitals
- **Search Integration**: Coordinate-based search for nearby hospitals

### Accessibility Features
- **Desktop**: Full interactive map with zoom controls
- **Mobile**: Responsive design with touch gestures
- **List View Fallback**: Always available as alternative view
- **Graceful Degradation**: Falls back to list view if API is unavailable

## User Experience

### For All Users
Users can now enjoy:
1. **List View** (Default)
   - Hospital cards with all details
   - Easy browsing and comparison
   - Works without API key

2. **Map View** (With API Key)
   - Visual location overview
   - Distance awareness
   - Geographic exploration
   - Click-and-explore hospital details

### Toggle Between Views
- Header buttons allow easy switching between List and Map views
- Both views show the same hospital data
- Compare button works in both modes

## Available Hospital Data on Map

Each hospital marker displays:
- **Name**: Official hospital name
- **Location**: Full address
- **Tier**: Visual indicator (color-coded)
- **Rating**: Patient satisfaction score
- **Cost Range**: Min-Max estimated cost
- **Specializations**: Medical specialties available
- **NABH Status**: Accreditation indicator
- **Directions**: One-click Google Maps link

## API Rate Limits

Google Maps API has usage limits. For production:
- Standard quota: 25,000 map loads per 24 hours (free tier)
- Consider upgrading if you expect high traffic
- Implement caching strategies for optimal performance

## Troubleshooting

### Map Not Loading
1. **Check API Key**: Verify in `.env.local` or Vercel dashboard
2. **Verify APIs Enabled**: Ensure Maps SDK and related APIs are active
3. **Check Domain Restrictions**: Confirm your domain is whitelisted
4. **Browser Console**: Check for CORS or authentication errors

### Markers Not Showing
- Verify hospital coordinates are valid (lat/lng format)
- Check map zoom level (adjust with `defaultZoom` prop)
- Inspect browser console for API errors

### Slow Performance
1. Use Map ID for custom styling
2. Implement marker clustering for large datasets
3. Cache API responses where possible
4. Optimize image loading

## For Administrators

### Updating API Key
```bash
# Update local environment
# Edit .env.local with new key

# Or update Vercel
npx vercel env list
npx vercel env remove NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
npx vercel env add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
```

### Monitoring Usage
- Track API usage in Google Cloud Console
- Monitor cost and quota
- Set up billing alerts

### Additional Customization

Edit `HospitalMap.tsx` to customize:
- Marker appearance: `HospitalMarker` component
- Info window content: `HospitalInfoContent` component
- Map styling: Add `mapId` for custom styling
- Default center and zoom: `center` and `defaultZoom` props

## Geographic Coverage

Current hospitals are configured for major Indian cities:
- **Tier 1**: Mumbai, Delhi, Bangalore, Hyderabad
- **Tier 2**: Nagpur, Raipur, बhopal, Indore, Surat, Patna
- **Tier 3**: Various cities across India

Coordinates are based on hospital headquarters or main branch.

## Next Steps

1. ✅ Local environment configured with `.env.local`
2. ✅ Vercel production environment configured
3. ✅ Map feature available to all users
4. Consider implementing:
   - Search by location functionality
   - Route optimization between hospitals
   - Real-time availability integration
   - Appointment booking from map

## Support & Documentation

- [Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript)
- [TenzorX Documentation](./instruction.md)
- [React Google Maps Library](https://visgl.github.io/react-google-maps/)
