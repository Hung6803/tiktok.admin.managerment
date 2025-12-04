# TikTok Video Upload API Research (2025)

## Video Upload Technical Specifications

### Supported File Formats
- Primary: MP4, MOV
- Secondary: MPEG, 3GP, AVI
- **Recommended**: MP4 with H.264 codec

### File Size Limits
- Android: Up to 72 MB
- iOS: Up to 287.6 MB
- Desktop/Web: Up to 500 MB
- Business Accounts: Up to 2 GB

### Video Resolution
- **Recommended**: 1080 × 1920 px (9:16 aspect ratio)
- **Minimum**: 720 × 1280 px
- Frame Rate: Up to 60 fps (30 fps typical)

## API Upload Process

### Authentication
- Requires approved `video.upload` scope
- Rate Limited: 6 requests per minute per access token

### Upload Endpoints
- Initialization: `https://open.tiktokapis.com/v2/post/publish/inbox/video/init/`
- Two Upload Methods:
  1. FILE_UPLOAD (local file)
  2. PULL_FROM_URL (remote video)

### Chunking Requirements
- Single chunk: ≤ 64 MB
- Multiple chunks: 1-1000 chunks possible
- Recommended for large files

## Publishing Controls

### Content Configuration
- Caption Length: Up to 2,200 characters
- Hashtag Support: Embedded in caption
- Privacy Levels:
  - PUBLIC_TO_EVERYONE
  - MUTUAL_FOLLOW_FRIENDS
  - SELF_ONLY

### Advanced Settings
- Disable Comments
- Disable Duet
- Disable Stitch
- Custom Video Cover
- Scheduled Publishing

## Error Handling

### Common Status Codes
- 200: Successful Request
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden (Scope/Permissions)
- 429: Rate Limited
- 500: Server Error

### Typical Error Scenarios
- Invalid File Format
- Oversized Video
- Insufficient Permissions
- Network Interruptions
- Processing Failures

## Best Practices
- Use H.264 video codec
- Maintain 1080×1920 resolution
- Compress videos efficiently
- Handle chunked uploads gracefully
- Implement comprehensive error tracking

## Unresolved Questions
- Exact processing time for different video sizes
- Complete list of unsupported video characteristics
- Detailed error message specifications

**Note**: Requires developer account approval and API audit for full functionality.