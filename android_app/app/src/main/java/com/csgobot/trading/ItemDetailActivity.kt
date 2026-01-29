package com.csgobot.trading

import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.csgobot.trading.api.ApiClient
import com.csgobot.trading.api.ItemPriceRequest
import com.csgobot.trading.api.RecommendationRequest
import com.csgobot.trading.databinding.ActivityItemDetailBinding
import kotlinx.coroutines.launch

/**
 * Item Detail Activity
 * Shows detailed information about a specific CS:GO item
 */
class ItemDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityItemDetailBinding
    private var itemName: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityItemDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Get item name from intent
        itemName = intent.getStringExtra("item_name") ?: ""
        if (itemName.isEmpty()) {
            finish()
            return
        }

        // Setup toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = itemName

        binding.toolbar.setNavigationOnClickListener {
            finish()
        }

        // Set item name
        binding.tvItemName.text = itemName

        // Load data
        loadItemData()
    }

    private fun loadItemData() {
        showLoading(true)

        lifecycleScope.launch {
            try {
                val authHeader = ApiClient.getAuthHeader()
                if (authHeader == null) {
                    showError("Authentication failed")
                    showLoading(false)
                    return@launch
                }

                // Load recommendation
                loadRecommendation(authHeader)

                // Load price data
                loadPriceData(authHeader)

            } catch (e: Exception) {
                e.printStackTrace()
                showError("Error loading data: ${e.message}")
            } finally {
                showLoading(false)
            }
        }
    }

    private suspend fun loadRecommendation(authHeader: String) {
        try {
            val response = ApiClient.getApi().getItemRecommendation(
                token = authHeader,
                request = RecommendationRequest(itemName)
            )

            if (response.isSuccessful) {
                val recommendation = response.body()
                if (recommendation != null) {
                    displayRecommendation(recommendation)
                }
            } else {
                showError("Failed to load recommendation")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            showError("Error loading recommendation")
        }
    }

    private suspend fun loadPriceData(authHeader: String) {
        try {
            val response = ApiClient.getApi().getItemPrice(
                token = authHeader,
                request = ItemPriceRequest(itemName, days = 30)
            )

            if (response.isSuccessful) {
                val priceData = response.body()
                if (priceData != null) {
                    displayPriceData(priceData)
                }
            } else {
                showError("Failed to load price data")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            showError("Error loading price data")
        }
    }

    private fun displayRecommendation(recommendation: com.csgobot.trading.api.RecommendationResponse) {
        binding.apply {
            // Recommendation
            tvRecommendation.text = recommendation.recommendation

            val recColor = when (recommendation.recommendation) {
                "BUY" -> Color.parseColor("#4CAF50") // Green
                "SELL" -> Color.parseColor("#F44336") // Red
                else -> Color.parseColor("#9E9E9E") // Gray
            }
            tvRecommendation.setTextColor(recColor)

            // Confidence
            val confidenceText = "${recommendation.confidence.toInt()}%"
            tvConfidence.text = confidenceText

            val confidenceColor = when {
                recommendation.confidence >= 80 -> Color.parseColor("#4CAF50")
                recommendation.confidence >= 60 -> Color.parseColor("#FFC107")
                else -> Color.parseColor("#FF9800")
            }
            tvConfidence.setTextColor(confidenceColor)

            // Trend
            if (recommendation.trend != null) {
                tvTrend.text = "Trend: ${recommendation.trend}"
            } else {
                tvTrend.visibility = View.GONE
            }

            // Reasons
            if (recommendation.reasons.isNotEmpty()) {
                val reasonsText = recommendation.reasons.joinToString("\n") { "• $it" }
                tvReasons.text = reasonsText
            } else {
                tvReasons.text = "No analysis reasons available"
            }
        }
    }

    private fun displayPriceData(priceData: com.csgobot.trading.api.ItemPriceResponse) {
        binding.apply {
            val priceInfoText = buildString {
                if (priceData.currentPrice != null) {
                    append("Current: $${String.format("%.2f", priceData.currentPrice)}\n")
                }
                if (priceData.avgPrice != null) {
                    append("Average: $${String.format("%.2f", priceData.avgPrice)}\n")
                }
                if (priceData.minPrice != null) {
                    append("Min: $${String.format("%.2f", priceData.minPrice)}\n")
                }
                if (priceData.maxPrice != null) {
                    append("Max: $${String.format("%.2f", priceData.maxPrice)}\n")
                }
                append("Data Points: ${priceData.dataPoints}")
            }

            tvPriceInfo.text = priceInfoText
        }
    }

    private fun showLoading(show: Boolean) {
        binding.progressBar.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
}
