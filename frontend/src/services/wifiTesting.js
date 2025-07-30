
export class WiFiTester {
    async testConnectivity() {
        try {
            const start = Date.now();
            // Use httpbin.org which allows CORS
            await fetch('https://httpbin.org/get', {
                method: 'GET',
                cache: 'no-cache'
            });
            const end = Date.now();

            return {
                connected: true,
                latency: end - start,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Connectivity test failed:', error);
            return {
                connected: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async measureSpeed() {
        try {
            // Use httpbin.org bytes endpoint which allows CORS
            const imageUrl = 'https://httpbin.org/bytes/50000'; 
            const fileSizeBytes = 50000;

            const startTime = Date.now();
            const response = await fetch(imageUrl);
            await response.blob();
            const endTime = Date.now();

            const durationMs = endTime - startTime;
            const durationSeconds = durationMs / 1000;
            const speedBps = fileSizeBytes / durationSeconds;
            const speedMbps = (speedBps * 8) / (1024 * 1024);

            return {
                speed: parseFloat(speedMbps.toFixed(2)),
                latency: durationMs,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Speed test failed:', error);
            return {
                speed: null,
                latency: null,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async gatherAutomaticData() {
        console.log('Starting automatic WiFi tests...');
        const data = {};

        console.log('Testing connectivity...');
        data.connectivity = await this.testConnectivity();
        console.log('Connectivity result:', data.connectivity);

        if (data.connectivity.connected) {
            console.log('Testing speed...');
            data.speed = await this.measureSpeed();
            console.log('Speed result:', data.speed);
        }

        if (navigator.connection) {
            data.connectionInfo = {
                type: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            };
            console.log('Connection info:', data.connectionInfo);
        }

        data.deviceType = /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'desktop';
        console.log('Final test data:', data);
        
        return data;
    }

    formatAutoTestResults(autoData) {
        return {
            connectivity: autoData.connectivity || { connected: false },
            speed: autoData.speed || { speed: 0, latency: 0 },
            connectionInfo: autoData.connectionInfo || { type: 'unknown' },
            deviceType: autoData.deviceType || 'unknown',
            test_timestamp: new Date().toISOString()
        };
    }
}

