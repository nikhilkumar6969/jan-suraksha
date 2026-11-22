package org.suraksha.sms

import android.app.Application
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.suraksha.sms.data.repository.SmsRepository
import org.suraksha.sms.notification.NotificationHelper

class SurakshaApp : Application() {

    override fun onCreate() {
        super.onCreate()
        
        // 1. Initialize High-Priority Notification Channel
        NotificationHelper.createNotificationChannel(this)

        // 2. Pre-load Offline Machine Learning Model into memory asynchronously
        CoroutineScope(Dispatchers.IO).launch {
            SmsRepository.getInstance(this@SurakshaApp)
        }
    }
}
