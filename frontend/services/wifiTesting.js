
export class WiFiTester {
    async testConnectivity() {
        try {
            const start = Date.now();
            await fetch('https://www.google.com/favicon.ico', {
                method: 'GET',
                mode: 'no-cors',
                cache: 'no-cache'
            });
            const end = Date.now();

            return {
                connected: true,
                latency: end - start,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                connected: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async measureSpeed() {
        try {
            const imageUrl = 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png';
            const fileSizeBytes = 13000;

            const startTime = Date.now();
            const response = await fetch(imageUrl + '?cache=' + Date.now());
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
            return {
                speed: null,
                latency: null,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async gatherAutomaticData() {
        const data = {};

        data.connectivity = await this.testConnectivity();

        if (data.connectivity.connected) {
            data.speed = await this.measureSpeed();
        }

        if (navigator.connection) {
            data.connectionInfo = {
                type: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            };
        }

        data.deviceType = /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : 'desktop';

        return data;
    }

    formatAutoTestResults(autoData) {
        return {
            connectivity_status: autoData.connectivity?.connected || fasle,
            speed_mbps: autoData.speed?.speed || null,
            latency_ms: autoData.connectivity?.latency || null,
            effective_connection_type: autoData.connectionInfo?.type || null,
            package_loss: null,
            test_timestamp: new Date().toISOString(),
            device_type: autoData.deviceType
        };
    }
}
