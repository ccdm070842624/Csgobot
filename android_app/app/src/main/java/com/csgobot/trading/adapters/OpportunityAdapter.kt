package com.csgobot.trading.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.csgobot.trading.api.OpportunityResponse
import com.csgobot.trading.databinding.ItemOpportunityBinding

/**
 * RecyclerView Adapter for Trading Opportunities
 */
class OpportunityAdapter(
    private val onItemClick: (OpportunityResponse) -> Unit
) : ListAdapter<OpportunityResponse, OpportunityAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemOpportunityBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding, onItemClick)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ViewHolder(
        private val binding: ItemOpportunityBinding,
        private val onItemClick: (OpportunityResponse) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(opportunity: OpportunityResponse) {
            binding.apply {
                // Item name
                tvItemName.text = opportunity.item

                // Confidence
                val confidenceText = "${opportunity.confidence.toInt()}%"
                tvConfidence.text = confidenceText

                // Set confidence color
                val confidenceColor = when {
                    opportunity.confidence >= 80 -> Color.parseColor("#4CAF50") // Green
                    opportunity.confidence >= 60 -> Color.parseColor("#FFC107") // Amber
                    else -> Color.parseColor("#FF9800") // Orange
                }
                tvConfidence.setTextColor(confidenceColor)

                // Recommendation badge
                tvRecommendation.text = opportunity.recommendation
                val badgeColor = when (opportunity.recommendation) {
                    "BUY" -> Color.parseColor("#4CAF50") // Green
                    "SELL" -> Color.parseColor("#F44336") // Red
                    else -> Color.parseColor("#9E9E9E") // Gray
                }
                tvRecommendation.setBackgroundColor(badgeColor)

                // Current price
                if (opportunity.currentPrice != null) {
                    tvCurrentPrice.text = "$${String.format("%.2f", opportunity.currentPrice)}"
                } else {
                    tvCurrentPrice.text = "N/A"
                }

                // Predicted price
                if (opportunity.predictedPrice != null) {
                    tvPredictedPrice.text = "$${String.format("%.2f", opportunity.predictedPrice)}"
                } else {
                    tvPredictedPrice.text = "N/A"
                }

                // Potential profit
                if (opportunity.potentialPercent != null) {
                    val sign = if (opportunity.potentialPercent > 0) "+" else ""
                    tvPotential.text = "$sign${String.format("%.1f", opportunity.potentialPercent)}%"

                    val potentialColor = if (opportunity.potentialPercent > 0) {
                        Color.parseColor("#4CAF50") // Green
                    } else {
                        Color.parseColor("#F44336") // Red
                    }
                    tvPotential.setTextColor(potentialColor)
                } else {
                    tvPotential.text = "N/A"
                }

                // Click listener
                root.setOnClickListener {
                    onItemClick(opportunity)
                }
            }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<OpportunityResponse>() {
        override fun areItemsTheSame(
            oldItem: OpportunityResponse,
            newItem: OpportunityResponse
        ): Boolean {
            return oldItem.item == newItem.item
        }

        override fun areContentsTheSame(
            oldItem: OpportunityResponse,
            newItem: OpportunityResponse
        ): Boolean {
            return oldItem == newItem
        }
    }
}
