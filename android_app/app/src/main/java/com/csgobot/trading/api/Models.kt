package com.csgobot.trading.api

import com.google.gson.annotations.SerializedName

/**
 * API Data Models
 */

// Authentication
data class TokenResponse(
    @SerializedName("token") val token: String,
    @SerializedName("expires_in") val expiresIn: Int
)

// Item Price Data
data class ItemPriceRequest(
    @SerializedName("item_name") val itemName: String,
    @SerializedName("days") val days: Int = 30
)

data class ItemPriceResponse(
    @SerializedName("item_name") val itemName: String,
    @SerializedName("current_price") val currentPrice: Double?,
    @SerializedName("avg_price") val avgPrice: Double?,
    @SerializedName("min_price") val minPrice: Double?,
    @SerializedName("max_price") val maxPrice: Double?,
    @SerializedName("data_points") val dataPoints: Int,
    @SerializedName("timestamp") val timestamp: String
)

// Recommendations
data class RecommendationRequest(
    @SerializedName("item_name") val itemName: String
)

data class RecommendationResponse(
    @SerializedName("item") val item: String,
    @SerializedName("recommendation") val recommendation: String, // BUY, SELL, HOLD
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("current_price") val currentPrice: Double?,
    @SerializedName("predicted_price") val predictedPrice: Double?,
    @SerializedName("trend") val trend: String?,
    @SerializedName("reasons") val reasons: List<String>,
    @SerializedName("timestamp") val timestamp: String
)

// Trading Opportunities
data class OpportunityResponse(
    @SerializedName("item") val item: String,
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("recommendation") val recommendation: String,
    @SerializedName("current_price") val currentPrice: Double?,
    @SerializedName("predicted_price") val predictedPrice: Double?,
    @SerializedName("potential_profit") val potentialProfit: Double?,
    @SerializedName("potential_percent") val potentialPercent: Double?,
    @SerializedName("data_points") val dataPoints: Int?
)

// Market Data Collection
data class MarketDataRequest(
    @SerializedName("items") val items: List<String>,
    @SerializedName("force_update") val forceUpdate: Boolean = false
)

data class MarketDataResponse(
    @SerializedName("status") val status: String,
    @SerializedName("items_processed") val itemsProcessed: Int,
    @SerializedName("success_count") val successCount: Int,
    @SerializedName("fail_count") val failCount: Int,
    @SerializedName("timestamp") val timestamp: String
)

// Statistics
data class StatsResponse(
    @SerializedName("total_items") val totalItems: Int,
    @SerializedName("items_with_data") val itemsWithData: Int,
    @SerializedName("total_data_points") val totalDataPoints: Int,
    @SerializedName("coverage_percent") val coveragePercent: Double,
    @SerializedName("timestamp") val timestamp: String
)

// Configuration
data class ConfigItemsResponse(
    @SerializedName("items") val items: List<String>,
    @SerializedName("count") val count: Int,
    @SerializedName("timestamp") val timestamp: String
)

// Health Check
data class HealthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("bot_initialized") val botInitialized: Boolean,
    @SerializedName("analyzer_initialized") val analyzerInitialized: Boolean,
    @SerializedName("timestamp") val timestamp: String
)

// Generic API Response
data class ApiResponse<T>(
    val success: Boolean,
    val data: T?,
    val error: String?
)
