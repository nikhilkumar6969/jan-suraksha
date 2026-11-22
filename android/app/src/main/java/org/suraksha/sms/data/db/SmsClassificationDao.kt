package org.suraksha.sms.data.db

import androidx.lifecycle.LiveData
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface SmsClassificationDao {

    @Query("SELECT * FROM sms_classifications ORDER BY timestamp DESC")
    fun getAllLive(): LiveData<List<SmsClassificationEntity>>

    @Query("SELECT * FROM sms_classifications ORDER BY timestamp DESC")
    suspend fun getAll(): List<SmsClassificationEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: SmsClassificationEntity): Long

    @Query("UPDATE sms_classifications SET userFeedback = :feedback WHERE id = :id")
    suspend fun updateFeedback(id: Long, feedback: String)

    @Query("SELECT COUNT(*) FROM sms_classifications WHERE classification = 'SPAM'")
    fun getSpamCountLive(): LiveData<Int>

    @Query("SELECT COUNT(*) FROM sms_classifications WHERE classification = 'SAFE'")
    fun getSafeCountLive(): LiveData<Int>

    @Query("SELECT COUNT(*) FROM sms_classifications")
    fun getTotalCountLive(): LiveData<Int>

    @Query("DELETE FROM sms_classifications")
    suspend fun clearAll()

    @Query("SELECT * FROM sms_classifications WHERE senderNumber = :sender ORDER BY timestamp DESC LIMIT 1")
    suspend fun getLatestBySender(sender: String): SmsClassificationEntity?
}
