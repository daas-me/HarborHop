# Video Assets

## Splash Animation

Place your splash screen animation video here with the name:
- `splash-animation.mp4`

### Video Requirements:
- **Format**: MP4 (H.264 codec recommended)
- **Duration**: 3-5 seconds recommended
- **Resolution**: 1920x1080 or 1280x720
- **File Size**: Keep under 5MB for fast loading

### How to Add Your Video:

1. Copy your video file to this folder
2. Rename it to `splash-animation.mp4`
3. The splash screen will automatically use it

### Alternative Formats:

If you want to use different formats, update the `splash.html` template:

```html
<video class="splash-video" id="splashVideo" autoplay muted playsinline>
    <source src="{% static 'videos/splash-animation.mp4' %}" type="video/mp4">
    <source src="{% static 'videos/splash-animation.webm' %}" type="video/webm">
    Your browser does not support the video tag.
</video>
```
