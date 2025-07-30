import { WiFiTester } from '../wifiTesting';

describe('WiFiTester', () => {
  let wifiTester;

  beforeEach(() => {
    wifiTester = new WiFiTester();
    // Mock navigator.connection
    Object.defineProperty(navigator, 'connection', {
      writable: true,
      value: {
        effectiveType: '4g',
        downlink: 10,
        rtt: 100
      }
    });
  });

  describe('formatAutoTestResults', () => {
    it('should format real browser test data correctly', () => {
      const mockData = {
        connectivity: { connected: true, latency: 45 },
        speed: { speed: 25.5, latency: 45 },
        connectionInfo: { type: 'wifi', downlink: 10, rtt: 45 },
        deviceType: 'desktop'
      };

      const result = wifiTester.formatAutoTestResults(mockData);

      expect(result).toEqual({
        connectivity: { connected: true },
        speed: { speed: 25.5, latency: 45 },
        connectionInfo: { type: 'wifi' },
        deviceType: 'desktop',
        test_timestamp: expect.any(String)
      });
    });

    it('should handle null values gracefully', () => {
      const mockData = {
        connectivity: null,
        speed: null,
        connectionInfo: null,
        deviceType: null
      };

      const result = wifiTester.formatAutoTestResults(mockData);

      expect(result).toEqual({
        connectivity: { connected: false },
        speed: { speed: 0, latency: 0 },
        connectionInfo: { type: 'unknown' },
        deviceType: 'unknown',
        test_timestamp: expect.any(String)
      });
    });

    it('should handle partial data', () => {
      const mockData = {
        connectivity: { connected: true },
        speed: { speed: 10.2 }
        // Missing connectionInfo and deviceType
      };

      const result = wifiTester.formatAutoTestResults(mockData);

      expect(result.connectivity.connected).toBe(true);
      expect(result.speed.speed).toBe(10.2);
      expect(result.connectionInfo.type).toBe('unknown');
      expect(result.deviceType).toBe('unknown');
    });
  });

  describe('gatherAutomaticData', () => {
    it('should return properly structured data', async () => {
      const result = await wifiTester.gatherAutomaticData();

      expect(result).toHaveProperty('connectivity');
      expect(result).toHaveProperty('speed');
      expect(result).toHaveProperty('connectionInfo');
      expect(result).toHaveProperty('deviceType');
      expect(typeof result.connectivity.connected).toBe('boolean');
      expect(typeof result.speed.speed).toBe('number');
      expect(typeof result.speed.latency).toBe('number');
    });
  });
});

// Mock tests for browser environment
if (typeof window !== 'undefined') {
  describe('Browser Tests', () => {
    it('should work in browser environment', () => {
      const tester = new WiFiTester();
      expect(tester).toBeInstanceOf(WiFiTester);
    });
  });
}
