/**
 * ChatterFix Relay Icon Generator
 * Generates all required app icons for iOS, Android, and Web
 */

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// ChatterFix brand colors
const COLORS = {
  primary: '#00d4ff',      // Cyan accent
  secondary: '#667eea',    // Purple gradient start
  background: '#1a1a2e',   // Dark navy
  backgroundAlt: '#16213e', // Slightly lighter navy
};

/**
 * Create a ChatterFix Relay app icon
 */
function createIcon(size, outputPath) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background - gradient effect (simulated with circle)
  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, size, size);

  // Rounded rectangle background for iOS style
  const cornerRadius = size * 0.22;
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, cornerRadius);
  ctx.fillStyle = COLORS.background;
  ctx.fill();

  // Add subtle gradient overlay
  const gradient = ctx.createRadialGradient(
    size * 0.3, size * 0.3, 0,
    size * 0.5, size * 0.5, size * 0.8
  );
  gradient.addColorStop(0, COLORS.backgroundAlt);
  gradient.addColorStop(1, COLORS.background);
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, cornerRadius);
  ctx.fillStyle = gradient;
  ctx.fill();

  // Draw wrench icon (🔧) - simplified geometric version
  const centerX = size / 2;
  const centerY = size / 2;
  const iconScale = size / 1024;

  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(-Math.PI / 4); // Rotate 45 degrees

  // Wrench handle
  ctx.fillStyle = COLORS.primary;
  const handleWidth = 80 * iconScale;
  const handleHeight = 350 * iconScale;
  ctx.beginPath();
  ctx.roundRect(-handleWidth/2, -50 * iconScale, handleWidth, handleHeight, handleWidth/2);
  ctx.fill();

  // Wrench head (open end)
  ctx.beginPath();
  ctx.arc(0, -150 * iconScale, 120 * iconScale, 0, Math.PI * 2);
  ctx.fill();

  // Cut out for wrench opening
  ctx.fillStyle = COLORS.background;
  ctx.beginPath();
  ctx.arc(0, -150 * iconScale, 60 * iconScale, 0, Math.PI * 2);
  ctx.fill();

  // Opening notch
  ctx.fillRect(-30 * iconScale, -260 * iconScale, 60 * iconScale, 110 * iconScale);

  ctx.restore();

  // Add "CF" text overlay
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${size * 0.15}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('CF', centerX, centerY + size * 0.28);

  // Add cyan accent ring
  ctx.strokeStyle = COLORS.primary;
  ctx.lineWidth = size * 0.02;
  ctx.beginPath();
  ctx.arc(centerX, centerY, size * 0.42, 0, Math.PI * 2);
  ctx.stroke();

  // Save to file
  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created: ${outputPath} (${size}x${size})`);
}

/**
 * Create adaptive icon foreground (Android)
 * Should have transparent areas for adaptive icon system
 */
function createAdaptiveIcon(size, outputPath) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Transparent background for adaptive icon
  ctx.clearRect(0, 0, size, size);

  const centerX = size / 2;
  const centerY = size / 2;
  const iconScale = size / 1024;

  // Draw wrench icon
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(-Math.PI / 4);

  // Wrench handle
  ctx.fillStyle = COLORS.primary;
  const handleWidth = 80 * iconScale;
  const handleHeight = 300 * iconScale;
  ctx.beginPath();
  ctx.roundRect(-handleWidth/2, -30 * iconScale, handleWidth, handleHeight, handleWidth/2);
  ctx.fill();

  // Wrench head
  ctx.beginPath();
  ctx.arc(0, -120 * iconScale, 100 * iconScale, 0, Math.PI * 2);
  ctx.fill();

  // Cut out
  ctx.globalCompositeOperation = 'destination-out';
  ctx.beginPath();
  ctx.arc(0, -120 * iconScale, 50 * iconScale, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillRect(-25 * iconScale, -220 * iconScale, 50 * iconScale, 100 * iconScale);

  ctx.restore();

  // "CF" text
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${size * 0.12}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('CF', centerX, centerY + size * 0.22);

  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created: ${outputPath} (${size}x${size}) [Adaptive]`);
}

/**
 * Create splash screen icon
 */
function createSplashIcon(size, outputPath) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Dark background
  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, size, size);

  const centerX = size / 2;
  const centerY = size / 2;
  const iconScale = size / 1024;

  // Large cyan accent circle
  ctx.strokeStyle = COLORS.primary;
  ctx.lineWidth = size * 0.015;
  ctx.beginPath();
  ctx.arc(centerX, centerY, size * 0.35, 0, Math.PI * 2);
  ctx.stroke();

  // Draw wrench
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(-Math.PI / 4);

  ctx.fillStyle = COLORS.primary;
  const handleWidth = 60 * iconScale;
  const handleHeight = 250 * iconScale;
  ctx.beginPath();
  ctx.roundRect(-handleWidth/2, -20 * iconScale, handleWidth, handleHeight, handleWidth/2);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(0, -100 * iconScale, 80 * iconScale, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = COLORS.background;
  ctx.beginPath();
  ctx.arc(0, -100 * iconScale, 40 * iconScale, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillRect(-20 * iconScale, -180 * iconScale, 40 * iconScale, 80 * iconScale);

  ctx.restore();

  // "ChatterFix" text
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${size * 0.08}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText('ChatterFix', centerX, centerY + size * 0.28);

  // "Relay" subtitle
  ctx.fillStyle = COLORS.primary;
  ctx.font = `${size * 0.05}px Arial, sans-serif`;
  ctx.fillText('RELAY', centerX, centerY + size * 0.36);

  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created: ${outputPath} (${size}x${size}) [Splash]`);
}

/**
 * Create favicon
 */
function createFavicon(size, outputPath) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background
  ctx.fillStyle = COLORS.background;
  ctx.beginPath();
  ctx.arc(size/2, size/2, size/2, 0, Math.PI * 2);
  ctx.fill();

  // Simple "CF" text for small icon
  ctx.fillStyle = COLORS.primary;
  ctx.font = `bold ${size * 0.45}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('CF', size/2, size/2);

  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created: ${outputPath} (${size}x${size}) [Favicon]`);
}

// Main execution
const assetsDir = path.join(__dirname, '..', 'assets');

console.log('\n🔧 Generating ChatterFix Relay Icons...\n');

// Main icons
createIcon(1024, path.join(assetsDir, 'icon.png'));
createAdaptiveIcon(1024, path.join(assetsDir, 'adaptive-icon.png'));
createSplashIcon(1024, path.join(assetsDir, 'splash-icon.png'));
createFavicon(48, path.join(assetsDir, 'favicon.png'));

// Additional PWA sizes
createIcon(192, path.join(assetsDir, 'icon-192.png'));
createIcon(512, path.join(assetsDir, 'icon-512.png'));
createIcon(180, path.join(assetsDir, 'apple-touch-icon.png'));

console.log('\n✅ All icons generated successfully!\n');
console.log('Icon locations:');
console.log('  - assets/icon.png (1024x1024 - iOS/General)');
console.log('  - assets/adaptive-icon.png (1024x1024 - Android)');
console.log('  - assets/splash-icon.png (1024x1024 - Splash Screen)');
console.log('  - assets/favicon.png (48x48 - Web)');
console.log('  - assets/icon-192.png (192x192 - PWA)');
console.log('  - assets/icon-512.png (512x512 - PWA)');
console.log('  - assets/apple-touch-icon.png (180x180 - iOS Safari)');
