export function getCelcius(kelvin) {
    return Math.round(kelvin - 273.15);
}

export function getFahrenheit(celsius) {
    return Math.round((celsius * 9) / 5 + 32);
}

export function getLocalTime(timestamp) {
    try {
        const date = new Date(timestamp * 1000);
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.log("Error getting local time:", error);
        return "Error";
    }
}