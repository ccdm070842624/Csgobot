package com.csgobot.trading

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.csgobot.trading.adapters.OpportunityAdapter
import com.csgobot.trading.api.ApiClient
import com.csgobot.trading.api.OpportunityResponse
import com.csgobot.trading.databinding.ActivityMainBinding
import kotlinx.coroutines.launch

/**
 * Main Activity
 * Displays trading opportunities and statistics
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var opportunityAdapter: OpportunityAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize ViewBinding
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Initialize API Client
        ApiClient.init(this)

        // Setup toolbar
        setSupportActionBar(binding.toolbar)

        // Setup RecyclerView
        setupRecyclerView()

        // Setup swipe refresh
        binding.swipeRefresh.setOnRefreshListener {
            loadData()
        }

        // Load initial data
        loadData()
    }

    private fun setupRecyclerView() {
        opportunityAdapter = OpportunityAdapter { opportunity ->
            // Item clicked
            val intent = Intent(this, ItemDetailActivity::class.java)
            intent.putExtra("item_name", opportunity.item)
            startActivity(intent)
        }

        binding.rvOpportunities.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = opportunityAdapter
        }
    }

    private fun loadData() {
        showLoading(true)

        lifecycleScope.launch {
            try {
                // Check health
                val healthResponse = ApiClient.getApi().healthCheck()
                if (!healthResponse.isSuccessful) {
                    showError("Server is not available")
                    showLoading(false)
                    return@launch
                }

                // Get auth header
                val authHeader = ApiClient.getAuthHeader()
                if (authHeader == null) {
                    showError("Failed to authenticate")
                    showLoading(false)
                    return@launch
                }

                // Load opportunities
                loadOpportunities(authHeader)

                // Load statistics
                loadStatistics(authHeader)

            } catch (e: Exception) {
                e.printStackTrace()
                showError("Error loading data: ${e.message}")
            } finally {
                showLoading(false)
                binding.swipeRefresh.isRefreshing = false
            }
        }
    }

    private suspend fun loadOpportunities(authHeader: String) {
        try {
            val response = ApiClient.getApi().getOpportunities(
                token = authHeader,
                limit = 10,
                minConfidence = 50
            )

            if (response.isSuccessful) {
                val opportunities = response.body()
                if (opportunities != null && opportunities.isNotEmpty()) {
                    opportunityAdapter.submitList(opportunities)
                } else {
                    showInfo("No trading opportunities found")
                }
            } else {
                showError("Failed to load opportunities: ${response.code()}")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            showError("Error loading opportunities: ${e.message}")
        }
    }

    private suspend fun loadStatistics(authHeader: String) {
        try {
            val response = ApiClient.getApi().getStatsSummary(authHeader)

            if (response.isSuccessful) {
                val stats = response.body()
                if (stats != null) {
                    val statsText = buildString {
                        append("Total Items: ${stats.totalItems}\n")
                        append("Items with Data: ${stats.itemsWithData}\n")
                        append("Total Data Points: ${stats.totalDataPoints}\n")
                        append("Coverage: ${"%.1f".format(stats.coveragePercent)}%")
                    }
                    binding.tvStats.text = statsText
                }
            } else {
                binding.tvStats.text = "Failed to load statistics"
            }
        } catch (e: Exception) {
            e.printStackTrace()
            binding.tvStats.text = "Error loading statistics"
        }
    }

    private fun showLoading(show: Boolean) {
        binding.progressBar.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }

    private fun showInfo(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_refresh -> {
                loadData()
                true
            }
            R.id.action_settings -> {
                // Open settings (to be implemented)
                Toast.makeText(this, "Settings", Toast.LENGTH_SHORT).show()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}
