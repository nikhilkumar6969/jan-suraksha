package org.suraksha.sms.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [SmsClassificationEntity::class], version = 1, exportSchema = false)
abstract class SurakshaDatabase : RoomDatabase() {

    abstract fun smsDao(): SmsClassificationDao

    companion object {
        @Volatile
        private var INSTANCE: SurakshaDatabase? = null

        fun getDatabase(context: Context): SurakshaDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    SurakshaDatabase::class.java,
                    "suraksha_sms_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
