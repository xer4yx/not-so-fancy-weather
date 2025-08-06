import axios from "axios";

const API_BASE_URL = "http://192.168.1.233:8668/api";

const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 5000, // 5 seconds timeout
    headers: {
        "Content-Type": "application/json",
    },
})

axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error("API Error:", error);
        return Promise.reject(error);
    }
);

export const getForecast = async (params = {}) => {
    try {
        // Filter out empty parameters
        const filteredParams = {};
        if (params.lat) filteredParams.lat = params.lat;
        if (params.lon) filteredParams.lon = params.lon;
        if (params.zipCode) filteredParams.zip_code = params.zipCode;
        if (params.cityName) filteredParams.city_name = params.cityName;
        if (params.cityId) filteredParams.city_id = params.cityId;

        const response = await axiosInstance.get("/weather/forecast", {
            params: filteredParams
        });
        console.log(response.data);
        return response.data;
    } catch (error) {
        if (error.code === "ERR_NETWORK") {
            throw new Error(
                "Oops! Cannot connect to the server right now. Try again later."
            );
        } else if (error.response) {
            throw new Error(
                error.response.data?.detail || "Sorry, no weather data found."
            );
        } else if (error.request) {
            throw new Error(
                "Something happened to your request. Try again later."
            );
        } else {
            throw new Error("Oops! Something went wrong. Try again later.");
        }
    }
}

export const login = async (username, password) => {
    try {
        const response = await axiosInstance.post('/api/login', {
            username,
            password
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response.data.detail);
    }
}
