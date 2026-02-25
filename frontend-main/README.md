# AI-Powered Two-Wheeler Business Growth Planner

A modern, responsive frontend dashboard for an AI-based business growth planner focused exclusively on two-wheeler businesses. This application provides data-driven insights for local MSMEs in the two-wheeler sector.

## Features

### 1. Main Dashboard
- Business type selection (Showroom, Service Centre, Spare Parts Shop)
- AI-generated one-time business strategy with recommendations
- KPI cards displaying Growth Score, Demand Level, and Risk Level
- Chatbot preview widget with quick access
- Location overview section

### 2. AI Chatbot
- Full-screen interactive chat interface
- Real-time message exchange with AI assistant
- Chat history with session management
- Suggested prompts for common questions
- Auto-scroll to latest messages

### 3. Analytics Page
- Animated bar charts showing demand vs growth comparison
- Smooth transitions and hover tooltips
- Backend-driven dynamic visualizations
- Business type filtering

### 4. Location Intelligence
- Interactive map with zoom and pan
- Location markers showing business insights
- Detailed area-level information on marker click
- Demand score indicators
- Location list with quick navigation

## Business Types

The system supports exactly three business types:
1. Two-Wheeler Showroom
2. Two-Wheeler Service Centre
3. Two-Wheeler Spare Parts Shop

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Maps**: Leaflet with React-Leaflet
- **Icons**: Lucide React
- **Build Tool**: Vite

## Project Structure

```
src/
├── components/
│   ├── Layout.tsx              # Main layout with navigation
│   └── BusinessTypeSelector.tsx # Business type selection component
├── pages/
│   ├── Dashboard.tsx           # Main dashboard page
│   ├── Chatbot.tsx            # Dedicated chatbot page
│   ├── Analytics.tsx          # Analytics with charts
│   └── Location.tsx           # Interactive map page
├── services/
│   └── api.ts                 # API service layer
├── App.tsx                    # Main app with routing
├── main.tsx                   # Entry point
└── index.css                  # Global styles

## Backend Integration

This frontend is designed to consume REST APIs from a Django backend.

### Required Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000/api
```

### API Endpoints Expected

The application expects the following endpoints from your Django backend:

1. **GET** `/business-types/` - Get list of business types
2. **POST** `/strategy/` - Get AI-generated strategy
   - Body: `{ businessType, location }`
3. **GET** `/kpi/?businessType=<type>` - Get KPI data
4. **POST** `/chat/` - Send chat message
   - Body: `{ message, sessionId }`
5. **GET** `/chat/history/?sessionId=<id>` - Get chat history
6. **GET** `/analytics/?businessType=<type>` - Get analytics data
7. **GET** `/locations/?businessType=<type>` - Get location data
8. **GET** `/locations/<id>/` - Get specific location insights

## Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (copy from `.env.example`)
4. Start the development server:
```bash
npm run dev
```

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Development

- **Dev Server**: `npm run dev`
- **Type Checking**: `npm run typecheck`
- **Linting**: `npm run lint`
- **Build**: `npm run build`

## Features Highlights

### Design
- Professional blue/green color palette
- Gradient backgrounds and smooth transitions
- Responsive design for all screen sizes
- Hover effects and loading states
- Clean, modern UI with card-based layouts

### User Experience
- Intuitive navigation between pages
- Clear visual hierarchy
- Real-time data updates
- Error handling with user-friendly messages
- Loading states for all async operations

### Code Quality
- TypeScript for type safety
- Modular component structure
- Clean API service layer
- Proper error handling
- Commented and maintainable code

## Usage

1. **Select Business Type**: Choose from the three available business types
2. **View Dashboard**: See AI-generated strategies and KPI metrics
3. **Chat with AI**: Get personalized business advice
4. **Analyze Data**: View demand and growth analytics
5. **Explore Locations**: Find optimal business locations on the map

## Notes for Backend Integration

- All API calls include proper error handling
- Loading states are implemented for better UX
- The frontend gracefully handles missing backend connections
- Session-based chat history management
- All data displays are dynamic and backend-driven

## Future Enhancements

- User authentication
- Data export functionality
- Custom date range filtering
- Advanced analytics with more chart types
- Mobile app version

## License

This project is designed for educational and startup demonstration purposes.
