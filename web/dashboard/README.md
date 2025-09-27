# SPIDER Dashboard

React-based web dashboard for the SPIDER Framework.

## Features

- **Modern React 18** with TypeScript
- **Material-UI** component library
- **Real-time updates** via WebSocket
- **Authentication** with JWT tokens
- **Responsive design** for mobile and desktop
- **Dark/Light theme** support
- **Real-time monitoring** and metrics

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- SPIDER API running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update environment variables in `.env`:
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_NAME=SPIDER Dashboard
```

4. Start development server:
```bash
npm start
```

The dashboard will be available at `http://localhost:3000`.

### Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Common/         # Common components (LoadingSpinner, ErrorBoundary)
│   ├── Dashboard/      # Dashboard-specific components
│   └── Layout/         # Layout components
├── contexts/           # React contexts
│   ├── AuthContext.tsx # Authentication context
│   └── WebSocketContext.tsx # WebSocket context
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── services/           # API services
├── theme.ts           # Material-UI theme
└── App.tsx            # Main application component
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Features

### Authentication
- JWT token-based authentication
- Automatic token refresh
- Session management
- Role-based access control

### Dashboard
- Real-time system metrics
- Performance monitoring
- Plugin management
- Alert system
- Recent activities

### Real-time Updates
- WebSocket connection for live data
- Automatic reconnection
- Real-time metrics updates
- Live alert notifications

### Responsive Design
- Mobile-first approach
- Adaptive layout
- Touch-friendly interface
- Cross-browser compatibility

## API Integration

The dashboard communicates with the SPIDER API through:

- **REST API** for CRUD operations
- **WebSocket** for real-time updates
- **JWT tokens** for authentication
- **Error handling** with retry logic

## Development

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout/Layout.tsx`

### Adding New Components

1. Create component in appropriate directory
2. Export from component directory
3. Import and use in pages

### API Services

Create new services in `src/services/` following the pattern:

```typescript
import { apiClient } from './apiClient';

class NewService {
  async getData(): Promise<any> {
    const response = await apiClient.get('/endpoint');
    return response.data.data;
  }
}

export const newService = new NewService();
```

## Deployment

The dashboard can be deployed as a static site or served by the FastAPI backend.

### Static Deployment

Build the project and serve the `build/` directory with any static file server.

### Integrated Deployment

The FastAPI backend can serve the React build files directly.

## Contributing

1. Follow the existing code style
2. Add TypeScript types for all props and functions
3. Use Material-UI components consistently
4. Write tests for new components
5. Update documentation

## License

Part of the SPIDER Framework project.
