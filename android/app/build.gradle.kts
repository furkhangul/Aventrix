plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "com.aventrix.device"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aventrix.device"
        // AccessibilityService.dispatchGesture needs API 24+; the
        // mediaProjection foreground-service type needs API 29+. 26 keeps
        // the manifest/permission model simple without excluding much.
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.0")
    implementation("androidx.activity:activity-ktx:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-service:2.8.7")
    // Bearer credential storage (device_secret) — Keystore-backed, never plain SharedPreferences.
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")

    // Actively maintained drop-in for Google's unpublished org.webrtc Maven
    // artifact — same org.webrtc.* API surface used throughout this module.
    implementation("io.getstream:stream-webrtc-android:1.3.5")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
}
