# Prep Pad Frontend 🍳

A modern React frontend for the Prep Pad cooking assistant, built with Material-UI and Framer Motion.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Backend server running on `http://localhost:8000`

### Installation & Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Open in browser:**
   ```
   http://localhost:3000
   ```

## 🛠️ Tech Stack

- **React 19.1.0** - Main frontend framework
- **TypeScript** - Type safety
- **Material-UI (MUI)** - UI component library
- **React Router DOM** - Client-side routing
- **Axios** - HTTP client for API calls
- **Framer Motion** - Animation library
- **React Type Animation** - Typing animations
- **Formik + Yup** - Form handling and validation

## 📁 Project Structure

```
frontend/src/
├── components/          # Reusable UI components
│   └── Navbar.tsx      # Navigation component
├── pages/              # Main application pages
│   ├── Home.tsx        # Landing page
│   ├── RecipeParser.tsx # Recipe parsing interface
│   ├── CookingSession.tsx # Active cooking session
│   └── RecipeLibrary.tsx # Saved recipes
├── services/           # API integration
│   └── api.ts         # API client and types
├── App.tsx            # Main app component
└── index.tsx         # Entry point
```

## 🎨 Features

### 🏠 Home Page
- Animated hero section with typing effect
- Feature showcase with hover animations
- Call-to-action buttons

### 🔍 Recipe Parser
- URL input with validation
- Real-time recipe parsing
- Optimized recipe display with prep/cook phases
- Ingredient lists and timing information

### 👨‍🍳 Cooking Session
- Step-by-step cooking guidance
- Voice command interface
- Quick action buttons
- Real-time session updates

### 📚 Recipe Library
- Grid view of saved recipes
- Recipe metadata (time, servings, difficulty)
- Quick start cooking buttons

## 🎭 Animations

- **Page transitions** with Framer Motion
- **Hover effects** on cards and buttons
- **Loading states** with smooth transitions
- **Typing animations** for dynamic text
- **Scale animations** for interactive elements

## 🔧 API Integration

The frontend communicates with the FastAPI backend through:

- **Recipe parsing** - `POST /api/parse_recipe`
- **Recipe management** - `GET /api/recipes`
- **Cooking sessions** - `POST /api/start_cooking/{id}`
- **Voice commands** - `POST /api/voice_command`

## 🎨 Theme & Styling

- **Custom Material-UI theme** with cooking colors
- **Orange primary** (#ff6b35) for cooking theme
- **Green secondary** (#4caf50) for success states
- **Responsive design** for all screen sizes
- **Consistent spacing** and typography

## 🚀 Development

### Available Scripts

```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### Environment Variables

Create `.env.local` for local development:
```
REACT_APP_API_URL=http://localhost:8000
```

## 🔧 Customization

### Adding New Pages
1. Create component in `src/pages/`
2. Add route in `App.tsx`
3. Update navigation in `Navbar.tsx`

### Styling Components
- Use Material-UI's `sx` prop for styling
- Follow the established theme colors
- Maintain consistent spacing with theme

### API Integration
- Add new endpoints in `src/services/api.ts`
- Use TypeScript interfaces for type safety
- Handle errors consistently

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deploy to Netlify/Vercel
1. Connect your GitHub repository
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Deploy!

### Environment Variables for Production
Set these in your deployment platform:
- `REACT_APP_API_URL` - Your backend API URL

## 🎯 Next Steps

- [ ] Add voice recognition for hands-free commands
- [ ] Implement real-time cooking timers
- [ ] Add recipe sharing functionality
- [ ] Create user authentication
- [ ] Add cooking progress tracking
- [ ] Implement offline support

---

**Prep Pad Frontend - Making cooking smarter, one recipe at a time!** 🍳