# EvidenceVault Mobile App - React Native & Flutter Guide

## Overview
The mobile app provides on-the-go evidence submission and monitoring for cyberbullying cases. Both React Native and Flutter implementations use the same backend API.

---

## React Native Implementation

### Setup

```bash
# Create React Native project
npx react-native init EvidenceVault

# Install dependencies
cd EvidenceVault
npm install axios react-native-camera react-native-file-picker react-native-image-picker react-native-geolocation-service @react-native-community/netinfo react-native-notifications

# For iOS
cd ios && pod install && cd ..
```

### Project Structure

```
mobile/
├── src/
│   ├── api/
│   │   ├── client.js          # API client wrapper
│   │   └── endpoints.js       # Vault API endpoints
│   ├── screens/
│   │   ├── HomeScreen.js
│   │   ├── SubmitEvidenceScreen.js
│   │   ├── CameraScreen.js
│   │   ├── DashboardScreen.js
│   │   └── SettingsScreen.js
│   ├── components/
│   │   ├── EvidenceCard.js
│   │   ├── ToxicityBadge.js
│   │   └── AnalyticsChart.js
│   ├── navigation/
│   │   └── RootNavigator.js
│   ├── services/
│   │   ├── encryption.js
│   │   ├── storage.js
│   │   └── analytics.js
│   └── App.js
├── app.json
└── package.json
```

### Key Features Implementation

#### 1. API Client (src/api/client.js)

```javascript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'http://your-api.com/api/v1';
const API_KEY = 'your-api-key';

class VaultAPIClient {
  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      }
    });
  }

  // Submit evidence
  async submitEvidence(evidence) {
    try {
      const response = await this.client.post('/webhooks/create-evidence', {
        ...evidence,
        timestamp: new Date().toISOString()
      });
      return response.data;
    } catch (error) {
      console.error('Submit error:', error);
      throw error;
    }
  }

  // Get real-time analysis
  async analyzeToxicity(content) {
    try {
      const response = await this.client.post('/realtime/analyze', {
        content: content,
        session_id: await this.getSessionId()
      });
      return response.data;
    } catch (error) {
      console.error('Analysis error:', error);
      throw error;
    }
  }

  // Get user dashboard
  async getDashboard(userId) {
    try {
      const response = await this.client.get(`/analytics/comprehensive-dashboard/${userId}`, {
        method: 'POST'
      });
      return response.data;
    } catch (error) {
      console.error('Dashboard error:', error);
      throw error;
    }
  }

  // Get submissions history
  async getSubmissions(userId) {
    try {
      const response = await this.client.get(`/bots/submissions`, {
        params: { user_id: userId }
      });
      return response.data;
    } catch (error) {
      console.error('History error:', error);
      throw error;
    }
  }

  private async getSessionId() {
    let sessionId = await AsyncStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      await AsyncStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }
}

export default new VaultAPIClient();
```

#### 2. Evidence Submission Screen (src/screens/SubmitEvidenceScreen.js)

```javascript
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert
} from 'react-native';
import { CameraRoll } from '@react-native-camera-roll/camera-roll';
import vaultAPI from '../api/client';

export const SubmitEvidenceScreen = ({ navigation }) => {
  const [content, setContent] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toxicityScore, setToxicityScore] = useState(null);

  const handleAnalyze = async () => {
    if (!content.trim()) {
      Alert.alert('Error', 'Please enter evidence text');
      return;
    }

    setLoading(true);
    try {
      const result = await vaultAPI.analyzeToxicity(content);
      setToxicityScore(result.max_toxicity);
    } catch (error) {
      Alert.alert('Error', 'Failed to analyze content');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      Alert.alert('Error', 'Please enter evidence');
      return;
    }

    setLoading(true);
    try {
      const evidence = {
        content: content,
        platform: 'mobile',
        media_url: selectedImage,
        toxicity_score: toxicityScore,
        metadata: {
          device_type: 'mobile',
          timestamp: new Date().toISOString()
        }
      };

      const result = await vaultAPI.submitEvidence(evidence);
      
      Alert.alert('Success', `Evidence submitted!\nID: ${result.evidence_id}`);
      setContent('');
      setSelectedImage(null);
      setToxicityScore(null);
    } catch (error) {
      Alert.alert('Error', 'Failed to submit evidence');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>
        Submit Evidence
      </Text>

      <TextInput
        style={{
          borderWidth: 1,
          borderColor: '#ddd',
          borderRadius: 8,
          padding: 12,
          marginBottom: 16,
          height: 120,
          textAlignVertical: 'top'
        }}
        placeholder="Enter evidence text..."
        value={content}
        onChangeText={setContent}
        multiline
      />

      {toxicityScore !== null && (
        <View style={{
          backgroundColor: toxicityScore > 0.7 ? '#ffebee' : '#fff8e1',
          padding: 12,
          borderRadius: 8,
          marginBottom: 16
        }}>
          <Text style={{ color: '#d32f2f', fontWeight: 'bold' }}>
            Toxicity: {(toxicityScore * 100).toFixed(1)}%
          </Text>
        </View>
      )}

      {selectedImage && (
        <Image
          source={{ uri: selectedImage }}
          style={{ width: '100%', height: 200, marginBottom: 16, borderRadius: 8 }}
        />
      )}

      <TouchableOpacity
        style={{
          backgroundColor: '#2196F3',
          padding: 12,
          borderRadius: 8,
          marginBottom: 8
        }}
        onPress={handleAnalyze}
        disabled={loading}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontWeight: 'bold' }}>
          {loading ? 'Analyzing...' : 'Analyze Text'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={{
          backgroundColor: '#4CAF50',
          padding: 12,
          borderRadius: 8
        }}
        onPress={handleSubmit}
        disabled={loading}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontWeight: 'bold' }}>
          {loading ? 'Submitting...' : 'Submit Evidence'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};
```

#### 3. Dashboard Screen (src/screens/DashboardScreen.js)

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, ActivityIndicator } from 'react-native';
import { LineChart, PieChart } from 'react-native-chart-kit';
import vaultAPI from '../api/client';

export const DashboardScreen = ({ userId }) => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, [userId]);

  const loadDashboard = async () => {
    try {
      const data = await vaultAPI.getDashboard(userId);
      setDashboard(data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" />;
  }

  if (!dashboard) {
    return <Text>Failed to load dashboard</Text>;
  }

  return (
    <ScrollView style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>
        Analytics Dashboard
      </Text>

      {/* Network Graph */}
      {dashboard.sections.network_graph && (
        <View style={{ marginBottom: 24 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
            Network Analysis
          </Text>
          <Text>
            Total Nodes: {dashboard.sections.network_graph.stats.node_count}
          </Text>
          <Text>
            Abusers Identified: {dashboard.sections.network_graph.stats.abuser_count}
          </Text>
        </View>
      )}

      {/* Escalation Predictions */}
      {dashboard.sections.escalation_predictions && (
        <View style={{ marginBottom: 24 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
            Risk Assessment
          </Text>
          <PieChart
            data={[
              { name: 'Critical', population: dashboard.sections.escalation_predictions.summary.critical, color: '#ff4444' },
              { name: 'High', population: dashboard.sections.escalation_predictions.summary.high, color: '#ff9800' },
              { name: 'Medium', population: dashboard.sections.escalation_predictions.summary.medium, color: '#ffc107' },
              { name: 'Low', population: dashboard.sections.escalation_predictions.summary.low, color: '#4CAF50' }
            ]}
            width={350}
            height={220}
            chartConfig={{ color: '#333' }}
            accessor="population"
            backgroundColor="transparent"
          />
        </View>
      )}

      {/* Heatmap Calendar */}
      {dashboard.sections.heatmap && (
        <View style={{ marginBottom: 24 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
            Incident Timeline
          </Text>
          <Text>
            Total Incidents: {dashboard.sections.heatmap.total_incidents}
          </Text>
          <Text>
            Average/Day: {dashboard.sections.heatmap.average_per_day.toFixed(1)}
          </Text>
          <Text>
            Peak: {dashboard.sections.heatmap.peak_date} ({dashboard.sections.heatmap.peak_count})
          </Text>
        </View>
      )}
    </ScrollView>
  );
};
```

---

## Flutter Implementation

### Setup

```bash
# Create Flutter project
flutter create evidence_vault

# Add dependencies to pubspec.yaml
flutter pub add http dio camera image_picker geolocation connectivity_plus charts path_provider sqflite

# Get packages
flutter pub get
```

### Project Structure

```
flutter_app/
├── lib/
│   ├── main.dart
│   ├── api/
│   │   ├── vault_client.dart
│   │   └── endpoints.dart
│   ├── screens/
│   │   ├── home_screen.dart
│   │   ├── submit_evidence_screen.dart
│   │   ├── camera_screen.dart
│   │   └── dashboard_screen.dart
│   ├── models/
│   │   ├── evidence.dart
│   │   └── analytics.dart
│   ├── widgets/
│   │   ├── evidence_card.dart
│   │   └── analytics_widget.dart
│   └── services/
│       ├── encryption_service.dart
│       └── storage_service.dart
├── pubspec.yaml
└── analysis_options.yaml
```

### Key Implementation (lib/api/vault_client.dart)

```dart
import 'package:dio/dio.dart';
import 'package:evidence_vault/models/evidence.dart';

class VaultAPIClient {
  late Dio _dio;
  static const String API_URL = 'http://your-api.com/api/v1';
  static const String API_KEY = 'your-api-key';

  VaultAPIClient() {
    _dio = Dio(BaseOptions(
      baseUrl: API_URL,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $API_KEY'
      },
    ));
  }

  // Submit evidence
  Future<Map<String, dynamic>> submitEvidence(Evidence evidence) async {
    try {
      final response = await _dio.post(
        '/webhooks/create-evidence',
        data: evidence.toJson(),
      );
      return response.data;
    } catch (e) {
      print('Error submitting evidence: $e');
      rethrow;
    }
  }

  // Analyze toxicity
  Future<Map<String, dynamic>> analyzeToxicity(String content) async {
    try {
      final response = await _dio.post(
        '/realtime/analyze',
        data: {
          'content': content,
          'session_id': DateTime.now().millisecondsSinceEpoch.toString()
        },
      );
      return response.data;
    } catch (e) {
      print('Error analyzing toxicity: $e');
      rethrow;
    }
  }

  // Get comprehensive dashboard
  Future<Map<String, dynamic>> getDashboard(String userId) async {
    try {
      final response = await _dio.post(
        '/analytics/comprehensive-dashboard/$userId',
        data: {},
      );
      return response.data;
    } catch (e) {
      print('Error fetching dashboard: $e');
      rethrow;
    }
  }

  // Get predictions
  Future<Map<String, dynamic>> getPredictiveEscalation(String userId, List<Map> profiles) async {
    try {
      final response = await _dio.post(
        '/analytics/predictive-escalation/$userId',
        data: { 'abuser_profiles': profiles },
      );
      return response.data;
    } catch (e) {
      print('Error fetching predictions: $e');
      rethrow;
    }
  }
}
```

---

## Installation & Setup

### For Users

1. **Download from App Store/Play Store** (when published)
   - iOS: App Store
   - Android: Google Play Store

2. **First Run Setup**
   - Create account with email
   - Set API endpoint (if using self-hosted)
   - Enable notifications

3. **Enable Permissions**
   - Camera (for screenshots)
   - Photos/Gallery access
   - Notifications

### For Developers

```bash
# React Native - iOS
cd ios && pod install && cd ..
react-native run-ios

# React Native - Android
react-native run-android

# Flutter - iOS
flutter run -d ios

# Flutter - Android
flutter run -d android
```

---

## Features

✅ **Real-time Evidence Capture**
- Screenshot capture
- Text submission
- Photo gallery import

✅ **Offline Support**
- Queue submissions when offline
- Sync when online

✅ **Encryption**
- End-to-end encryption
- Secure local storage

✅ **Analytics**
- View incident patterns
- Track escalation risk
- Network visualization

✅ **Notifications**
- Real-time alerts
- Evidence submission confirmations

---

## API Integration

All mobile apps use the same backend API endpoints:

- `POST /api/v1/webhooks/create-evidence` - Submit evidence
- `POST /api/v1/realtime/analyze` - Analyze content
- `GET /api/v1/analytics/comprehensive-dashboard/{user_id}` - Get dashboard
- `POST /api/v1/analytics/predictive-escalation/{user_id}` - Get predictions

---

## Environment Variables

Create `.env` file:

```
VAULT_API_URL=http://your-api.com
API_KEY=your-api-key
ENABLE_ANALYTICS=true
ENABLE_NOTIFICATIONS=true
```

---

## Troubleshooting

### Build Issues
- Clear build cache: `flutter clean` / `npm cache clean`
- Update SDK: `flutter upgrade`

### API Connection
- Verify API URL is correct
- Check API key in environment
- Ensure backend is running

### Camera/Permissions
- Grant permissions in app settings
- For iOS, update Info.plist
- For Android, check AndroidManifest.xml
