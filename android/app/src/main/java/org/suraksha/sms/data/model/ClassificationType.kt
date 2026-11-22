package org.suraksha.sms.data.model

enum class ClassificationType {
    SPAM,
    SAFE,
    UNSURE
}

enum class UserFeedback {
    NONE,
    MARKED_SAFE,
    MARKED_SPAM
}
