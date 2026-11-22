package org.suraksha.sms.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.suraksha.sms.data.db.SmsClassificationEntity
import org.suraksha.sms.data.model.UserFeedback
import org.suraksha.sms.data.repository.SmsRepository
import org.suraksha.sms.ml.PredictionResult

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = SmsRepository.getInstance(application)

    val allClassifications: LiveData<List<SmsClassificationEntity>> = repository.allClassifications
    val spamCount: LiveData<Int> = repository.spamCount
    val safeCount: LiveData<Int> = repository.safeCount
    val totalCount: LiveData<Int> = repository.totalCount

    private val _manualTestResult = MutableLiveData<PredictionResult?>()
    val manualTestResult: LiveData<PredictionResult?> = _manualTestResult

    fun isModelReady(): Boolean = repository.isModelReady()

    fun getModelFeaturesCount(): Int = repository.getModelFeaturesCount()

    fun updateFeedback(id: Long, feedback: UserFeedback) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.updateFeedback(id, feedback)
        }
    }

    fun clearHistory() {
        viewModelScope.launch(Dispatchers.IO) {
            repository.clearHistory()
        }
    }

    fun testManualMessage(sender: String, messageText: String) {
        viewModelScope.launch(Dispatchers.IO) {
            val (_, prediction) = repository.processIncomingSms(sender, messageText)
            _manualTestResult.postValue(prediction)
        }
    }
}
