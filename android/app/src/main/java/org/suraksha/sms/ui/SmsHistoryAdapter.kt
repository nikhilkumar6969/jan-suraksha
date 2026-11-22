package org.suraksha.sms.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import org.suraksha.sms.R
import org.suraksha.sms.data.db.SmsClassificationEntity
import org.suraksha.sms.data.model.UserFeedback
import org.suraksha.sms.databinding.ItemSmsHistoryBinding
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class SmsHistoryAdapter(
    private val onFeedbackClick: (entity: SmsClassificationEntity, feedback: UserFeedback) -> Unit
) : ListAdapter<SmsClassificationEntity, SmsHistoryAdapter.SmsViewHolder>(DiffCallback) {

    private val expandedItems = mutableSetOf<Long>()
    private val dateFormat = SimpleDateFormat("dd MMM, hh:mm a", Locale.getDefault())

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SmsViewHolder {
        val binding = ItemSmsHistoryBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return SmsViewHolder(binding)
    }

    override fun onBindViewHolder(holder: SmsViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class SmsViewHolder(private val binding: ItemSmsHistoryBinding) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: SmsClassificationEntity) {
            val context = binding.root.context
            binding.txtSender.text = item.senderNumber
            binding.txtTimestamp.text = dateFormat.format(Date(item.timestamp))

            val isSpam = item.classification.equals("SPAM", ignoreCase = true)
            val confidencePct = if (isSpam) {
                (item.predictionScore * 100).toInt()
            } else {
                ((1.0f - item.predictionScore) * 100).toInt()
            }.coerceIn(50, 100)

            if (isSpam) {
                binding.imgBadgeIcon.setImageResource(R.drawable.ic_spam_warning)
                binding.txtBadgePill.text = "SPAM $confidencePct%"
                binding.txtBadgePill.setTextColor(ContextCompat.getColor(context, R.color.color_danger))
                binding.txtBadgePill.backgroundTintList = ContextCompat.getColorStateList(context, R.color.color_danger_bg)
            } else {
                binding.imgBadgeIcon.setImageResource(R.drawable.ic_safe_check)
                binding.txtBadgePill.text = "SAFE $confidencePct%"
                binding.txtBadgePill.setTextColor(ContextCompat.getColor(context, R.color.color_safe))
                binding.txtBadgePill.backgroundTintList = ContextCompat.getColorStateList(context, R.color.color_safe_bg)
            }

            // Message text truncation or full
            val isExpanded = expandedItems.contains(item.id)
            if (isExpanded || item.messageBody.length <= 100) {
                binding.txtMessageBody.text = item.messageBody
                binding.txtMessageBody.maxLines = Int.MAX_VALUE
            } else {
                binding.txtMessageBody.text = item.messageBody.substring(0, 97) + "..."
                binding.txtMessageBody.maxLines = 3
            }

            binding.txtMessageBody.setOnClickListener {
                if (expandedItems.contains(item.id)) {
                    expandedItems.remove(item.id)
                } else {
                    expandedItems.add(item.id)
                }
                notifyItemChanged(bindingAdapterPosition)
            }

            // Detected rules tag
            if (item.detectedRules.isNotBlank()) {
                binding.txtRuleTags.visibility = View.VISIBLE
                binding.txtRuleTags.text = "Rules: ${item.detectedRules}"
            } else {
                binding.txtRuleTags.visibility = View.GONE
            }

            // Feedback controls
            when (item.userFeedback) {
                UserFeedback.MARKED_SAFE.name -> {
                    binding.btnMarkSafe.text = "Marked Safe ✓"
                    binding.btnMarkSafe.isEnabled = false
                    binding.btnMarkSpam.isEnabled = true
                }
                UserFeedback.MARKED_SPAM.name -> {
                    binding.btnMarkSpam.text = "Reported Spam ✓"
                    binding.btnMarkSpam.isEnabled = false
                    binding.btnMarkSafe.isEnabled = true
                }
                else -> {
                    binding.btnMarkSafe.text = "Mark Safe"
                    binding.btnMarkSafe.isEnabled = true
                    binding.btnMarkSpam.text = "Report Spam"
                    binding.btnMarkSpam.isEnabled = true
                }
            }

            binding.btnMarkSafe.setOnClickListener {
                onFeedbackClick(item, UserFeedback.MARKED_SAFE)
            }

            binding.btnMarkSpam.setOnClickListener {
                onFeedbackClick(item, UserFeedback.MARKED_SPAM)
            }
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<SmsClassificationEntity>() {
        override fun areItemsTheSame(oldItem: SmsClassificationEntity, newItem: SmsClassificationEntity): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: SmsClassificationEntity, newItem: SmsClassificationEntity): Boolean {
            return oldItem == newItem
        }
    }
}
