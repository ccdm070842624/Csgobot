package com.csgobot.trading.api

import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit API Service Interface
 */
interface TradingApi {

    // Authentication
    @POST("auth/token")
    suspend fun getToken(): Response<TokenResponse>

    // Health Check
    @GET("health")
    suspend fun healthCheck(): Response<HealthResponse>

    // Market Data
    @POST("api/market/collect")
    suspend fun collectMarketData(
        @Header("Authorization") token: String,
        @Body request: MarketDataRequest
    ): Response<MarketDataResponse>

    @POST("api/market/price")
    suspend fun getItemPrice(
        @Header("Authorization") token: String,
        @Body request: ItemPriceRequest
    ): Response<ItemPriceResponse>

    // Recommendations
    @POST("api/recommendations/item")
    suspend fun getItemRecommendation(
        @Header("Authorization") token: String,
        @Body request: RecommendationRequest
    ): Response<RecommendationResponse>

    @GET("api/recommendations/opportunities")
    suspend fun getOpportunities(
        @Header("Authorization") token: String,
        @Query("limit") limit: Int = 10,
        @Query("min_confidence") minConfidence: Int = 50
    ): Response<List<OpportunityResponse>>

    // Statistics
    @GET("api/stats/summary")
    suspend fun getStatsSummary(
        @Header("Authorization") token: String
    ): Response<StatsResponse>

    // Configuration
    @GET("api/config/items")
    suspend fun getConfiguredItems(
        @Header("Authorization") token: String
    ): Response<ConfigItemsResponse>
}
