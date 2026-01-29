package com.csgobot.trading.api

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.csgobot.trading.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * API Client Singleton
 * Manages API communication and authentication
 */
object ApiClient {

    private var api: TradingApi? = null
    private var sharedPrefs: SharedPreferences? = null
    private var cachedToken: String? = null

    private const val PREF_NAME = "csgo_bot_prefs"
    private const val KEY_API_TOKEN = "api_token"
    private const val KEY_TOKEN_EXPIRY = "token_expiry"

    /**
     * Initialize API client
     */
    fun init(context: Context) {
        // Initialize encrypted SharedPreferences
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        sharedPrefs = EncryptedSharedPreferences.create(
            context,
            PREF_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )

        // Load cached token
        cachedToken = sharedPrefs?.getString(KEY_API_TOKEN, null)
    }

    /**
     * Get API service instance
     */
    fun getApi(): TradingApi {
        if (api == null) {
            api = createApi()
        }
        return api!!
    }

    /**
     * Create Retrofit API instance
     */
    private fun createApi(): TradingApi {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        return retrofit.create(TradingApi::class.java)
    }

    /**
     * Get authentication token (from cache or request new)
     */
    suspend fun getToken(): String? {
        // Check if cached token is still valid
        if (cachedToken != null && !isTokenExpired()) {
            return cachedToken
        }

        // Request new token
        try {
            val response = getApi().getToken()
            if (response.isSuccessful) {
                val tokenResponse = response.body()
                if (tokenResponse != null) {
                    cachedToken = tokenResponse.token
                    saveToken(tokenResponse.token, tokenResponse.expiresIn)
                    return tokenResponse.token
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        return null
    }

    /**
     * Get authorization header value
     */
    suspend fun getAuthHeader(): String? {
        val token = getToken()
        return if (token != null) "Bearer $token" else null
    }

    /**
     * Save token to encrypted storage
     */
    private fun saveToken(token: String, expiresIn: Int) {
        val expiryTime = System.currentTimeMillis() + (expiresIn * 1000L)
        sharedPrefs?.edit()?.apply {
            putString(KEY_API_TOKEN, token)
            putLong(KEY_TOKEN_EXPIRY, expiryTime)
            apply()
        }
    }

    /**
     * Check if token is expired
     */
    private fun isTokenExpired(): Boolean {
        val expiryTime = sharedPrefs?.getLong(KEY_TOKEN_EXPIRY, 0) ?: 0
        return System.currentTimeMillis() >= expiryTime
    }

    /**
     * Clear cached token
     */
    fun clearToken() {
        cachedToken = null
        sharedPrefs?.edit()?.apply {
            remove(KEY_API_TOKEN)
            remove(KEY_TOKEN_EXPIRY)
            apply()
        }
    }

    /**
     * Update API base URL
     */
    fun updateBaseUrl(context: Context, newUrl: String) {
        // Reset API instance to force recreation with new URL
        api = null
        // In production, you'd need to rebuild Retrofit with new base URL
    }
}
