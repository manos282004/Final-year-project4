# Backend API Documentation

This document outlines the expected API endpoints that the Django backend should implement.

## Base URL

```
http://localhost:8000/api
```

Configure in `.env` file using `VITE_API_URL`

## Authentication

Currently, no authentication is implemented. Future versions may include JWT or session-based auth.

## API Endpoints

### 1. Get Business Types

**Endpoint**: `GET /business-types/`

**Description**: Returns the list of available business types.

**Response**:
```json
[
  {
    "id": "showroom",
    "name": "Two-Wheeler Showroom"
  },
  {
    "id": "service",
    "name": "Two-Wheeler Service Centre"
  },
  {
    "id": "spares",
    "name": "Two-Wheeler Spare Parts Shop"
  }
]
```

---

### 2. Get Business Strategy

**Endpoint**: `POST /strategy/`

**Description**: Returns AI-generated business strategy based on business type and location.

**Request Body**:
```json
{
  "businessType": "showroom",
  "location": "default"
}
```

**Response**:
```json
{
  "id": "strategy-1",
  "title": "Urban Showroom Strategy",
  "description": "Focus on premium models in high-traffic urban areas with strong digital presence",
  "recommendations": [
    "Establish presence in commercial zones near main roads",
    "Partner with finance companies for easy EMI options",
    "Invest in digital marketing and social media presence",
    "Offer test rides and comparison tools"
  ]
}
```

---

### 3. Get KPI Data

**Endpoint**: `GET /kpi/?businessType=<type>`

**Description**: Returns key performance indicators for the selected business type.

**Query Parameters**:
- `businessType`: Business type ID (required)

**Response**:
```json
{
  "growthScore": 75,
  "demandLevel": "High",
  "riskLevel": "Medium",
  "insight": "The two-wheeler market in this region shows strong growth potential with increasing urbanization and demand for personal mobility."
}
```

---

### 4. Send Chat Message

**Endpoint**: `POST /chat/`

**Description**: Sends a message to the AI chatbot and receives a response.

**Request Body**:
```json
{
  "message": "What are the best locations for a showroom?",
  "sessionId": "session-1234567890"
}
```

**Response**:
```json
{
  "id": "msg-1234567891",
  "role": "assistant",
  "content": "The best locations for a two-wheeler showroom are typically near main roads with high visibility, in commercial areas with good foot traffic, and close to residential neighborhoods. Consider factors like parking availability, competitor proximity, and local demographics.",
  "timestamp": "2024-01-12T10:30:00.000Z"
}
```

---

### 5. Get Chat History

**Endpoint**: `GET /chat/history/?sessionId=<id>`

**Description**: Retrieves the chat history for a specific session.

**Query Parameters**:
- `sessionId`: Session identifier (required)

**Response**:
```json
[
  {
    "id": "msg-1",
    "role": "user",
    "content": "What are the best locations?",
    "timestamp": "2024-01-12T10:29:00.000Z"
  },
  {
    "id": "msg-2",
    "role": "assistant",
    "content": "The best locations are...",
    "timestamp": "2024-01-12T10:30:00.000Z"
  }
]
```

---

### 6. Get Analytics Data

**Endpoint**: `GET /analytics/?businessType=<type>`

**Description**: Returns analytics data for charts showing demand and growth metrics.

**Query Parameters**:
- `businessType`: Business type ID (required)

**Response**:
```json
{
  "categories": ["North Zone", "South Zone", "East Zone", "West Zone", "Central"],
  "demand": [85, 72, 68, 90, 78],
  "growth": [65, 80, 75, 70, 85]
}
```

---

### 7. Get Locations

**Endpoint**: `GET /locations/?businessType=<type>`

**Description**: Returns a list of strategic locations with their coordinates and insights.

**Query Parameters**:
- `businessType`: Business type ID (required)

**Response**:
```json
[
  {
    "id": "loc-1",
    "name": "Commercial Hub - MG Road",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "insights": "High footfall area with excellent visibility. Strong demand for premium two-wheelers. Moderate competition.",
    "demandScore": 85
  },
  {
    "id": "loc-2",
    "name": "Residential Area - Sector 18",
    "latitude": 28.6304,
    "longitude": 77.2177,
    "insights": "Growing residential area with increasing demand for family-oriented two-wheelers. Low competition.",
    "demandScore": 72
  }
]
```

---

### 8. Get Location Details

**Endpoint**: `GET /locations/<id>/`

**Description**: Returns detailed insights for a specific location.

**Response**:
```json
{
  "id": "loc-1",
  "name": "Commercial Hub - MG Road",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "insights": "High footfall area with excellent visibility. Strong demand for premium two-wheelers. Moderate competition. Average property rent: ₹50,000/month. Expected monthly footfall: 10,000+",
  "demandScore": 85
}
```

---

## Error Handling

All endpoints should return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format**:
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": "Additional error details if available"
}
```

## CORS Configuration

Ensure your Django backend allows CORS requests from the frontend:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
]
```

## Rate Limiting

Consider implementing rate limiting for:
- Chat endpoint: 20 requests/minute
- Analytics endpoint: 100 requests/hour

## Data Requirements

### Business Types (Fixed)
The system must support exactly these three types:
1. Two-Wheeler Showroom
2. Two-Wheeler Service Centre
3. Two-Wheeler Spare Parts Shop

### Coordinates
- All location coordinates should be valid latitude/longitude pairs
- Default center: New Delhi area (28.6139, 77.2090)

### Chat Messages
- Store chat history per session
- Implement session cleanup after 24 hours
- Maximum message length: 1000 characters

## Testing

Test the API endpoints using tools like:
- Postman
- curl
- Django REST Framework browsable API

Example curl request:
```bash
curl -X POST http://localhost:8000/api/strategy/ \
  -H "Content-Type: application/json" \
  -d '{"businessType":"showroom","location":"default"}'
```

## Performance Considerations

- Implement caching for frequently accessed data (KPI, analytics)
- Use database indexing for location queries
- Optimize AI response generation to respond within 3 seconds
- Implement pagination for chat history if needed

## Security

- Validate all input parameters
- Sanitize user messages before processing
- Implement SQL injection prevention
- Use parameterized queries
- Add request size limits
