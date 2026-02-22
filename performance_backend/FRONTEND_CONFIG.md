# Frontend Configuration Guide

## API Endpoint Configuration

The frontend service file (`aiPerformanceAnalysisService.ts` or similar) should point to the correct endpoint:

### Development (Local)
```typescript
const API_BASE_URL = 'http://localhost:8000';
const response = await fetch(`${API_BASE_URL}/analyze-performance`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(performanceData)
});
```

### Production (Deployed)
```typescript
// Option 1: Environment Variable (Recommended)
const API_BASE_URL = process.env.REACT_APP_PERFORMANCE_API_URL || 'https://paaibackend-development.up.railway.app';

// Option 2: Direct Configuration
const API_BASE_URL = 'https://paaibackend-development.up.railway.app';

const response = await fetch(`${API_BASE_URL}/analyze-performance`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(performanceData)
});
```

## Request Format

The endpoint expects a POST request to `/analyze-performance` with the following body:

```typescript
interface PerformanceRequest {
  user_id: string;
  current_score: number;
  previous_score?: number;
  performance_band: "Excellent" | "Very Good" | "Good" | "Average" | "Needs Attention";
  weekly_history?: Array<{ week: string; score: number }>;
  productivity: number;
  consistency: number;
  quality: number;
  overdue_rate: number;
}
```

## Response Format

```typescript
interface PerformanceResponse {
  trend: "Improving" | "Declining" | "Stable";
  risk_state: "Improving" | "Needs Attention" | "Stable";
  patterns: string[];
  professional_summary: string;
  data_analysis: string;
  supportive_interpretation: string;
  actionable_suggestions: string;
}
```

## Important Notes

1. **Endpoint Path**: Make sure you're using `/analyze-performance` (not `/analyze`)
2. **CORS**: The backend allows all origins, so CORS should not be an issue
3. **Timeout**: The first request after server start may take ~30 seconds due to model loading. Set your frontend timeout to at least 60 seconds.
4. **Model Ready**: Check server logs for "✅ FLAN-T5 model loaded and ready" before making requests
