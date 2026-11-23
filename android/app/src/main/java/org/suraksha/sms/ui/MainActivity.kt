package org.suraksha.sms.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.addCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.webkit.WebViewAssetLoader
import org.suraksha.sms.R
import org.suraksha.sms.bridge.SurakshaNativeBridge
import org.suraksha.sms.data.model.UserFeedback
import org.suraksha.sms.databinding.ActivityMainBinding
import org.suraksha.sms.notification.NotificationHelper

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: MainViewModel by viewModels()
    private lateinit var historyAdapter: SmsHistoryAdapter
    private var isDashboardViewActive = true
    private var assetLoader: WebViewAssetLoader? = null

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val smsGranted = permissions[Manifest.permission.RECEIVE_SMS] ?: false
        val audioGranted = permissions[Manifest.permission.RECORD_AUDIO] ?: false

        if (smsGranted) {
            updatePermissionUi(true)
            Toast.makeText(this, "SMS Detection Activated. Incoming messages will be scanned offline.", Toast.LENGTH_LONG).show()
        } else {
            updatePermissionUi(false)
        }

        if (audioGranted) {
            Toast.makeText(this, "Microphone Access Granted for Offline Call Guardian.", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupRecyclerView()
        observeViewModel()
        setupListeners()
        setupWebViewDashboard()
        checkPermissions()
        handleIncomingIntent(intent)

        // Handle back button navigation inside WebView with double-tap exit prevention
        var backPressedOnce = false
        onBackPressedDispatcher.addCallback(this) {
            if (isDashboardViewActive && binding.webViewDashboard.canGoBack()) {
                binding.webViewDashboard.goBack()
            } else if (!isDashboardViewActive) {
                // Switch back to dashboard view
                toggleMainView()
            } else {
                if (backPressedOnce) {
                    finish()
                } else {
                    backPressedOnce = true
                    Toast.makeText(this@MainActivity, "Press BACK again to exit Jan Suraksha", Toast.LENGTH_SHORT).show()
                    binding.root.postDelayed({ backPressedOnce = false }, 2000)
                }
            }
        }
    }

    private fun setupWebViewDashboard() {
        val webView = binding.webViewDashboard

        // Initialize WebViewAssetLoader for secure offline asset serving without file:// restrictions
        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.mediaPlaybackRequiresUserGesture = false // Smooth offline audio warnings
        settings.cacheMode = WebSettings.LOAD_DEFAULT
        settings.databaseEnabled = true

        // Attach Secure Native Hardware Bridge
        webView.addJavascriptInterface(
            SurakshaNativeBridge(this, this),
            SurakshaNativeBridge.BRIDGE_NAME
        )

        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                val resources = request.resources
                if (resources.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) {
                    // Check Android RECORD_AUDIO permission
                    if (ContextCompat.checkSelfPermission(this@MainActivity, Manifest.permission.RECORD_AUDIO)
                        == PackageManager.PERMISSION_GRANTED) {
                        request.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                    } else {
                        requestPermissionLauncher.launch(arrayOf(Manifest.permission.RECORD_AUDIO))
                        request.deny()
                    }
                } else {
                    request.deny()
                }
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView?,
                request: WebResourceRequest?
            ): WebResourceResponse? {
                request?.url?.let { uri ->
                    val response = assetLoader?.shouldInterceptRequest(uri)
                    if (response != null) return response
                }
                return super.shouldInterceptRequest(view, request)
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                super.onReceivedError(view, errorCode, description, failingUrl)
                // Fallback to direct asset loading if AssetLoader encounters scheme mismatch
                if (failingUrl?.startsWith("https://appassets.androidplatform.net") == true) {
                    view?.loadUrl("file:///android_asset/public/index.html")
                }
            }
        }

        // Primary: Load bundled offline dashboard
        webView.loadUrl("file:///android_asset/public/index.html")
    }

    private fun toggleMainView() {
        isDashboardViewActive = !isDashboardViewActive
        if (isDashboardViewActive) {
            binding.webViewDashboard.visibility = View.VISIBLE
            binding.viewSmsHistory.visibility = View.GONE
            binding.btnToggleView.setImageResource(R.drawable.ic_shield)
            binding.btnToggleView.contentDescription = "Show Native SMS History"
        } else {
            binding.webViewDashboard.visibility = View.GONE
            binding.viewSmsHistory.visibility = View.VISIBLE
            binding.btnToggleView.setImageResource(R.drawable.ic_shield)
            binding.btnToggleView.contentDescription = "Show Web Dashboard"
        }
    }

    override fun onResume() {
        super.onResume()
        binding.webViewDashboard.onResume()
    }

    override fun onPause() {
        super.onPause()
        binding.webViewDashboard.onPause()
    }

    override fun onDestroy() {
        binding.webViewDashboard.destroy()
        super.onDestroy()
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIncomingIntent(it) }
    }

    private fun handleIncomingIntent(intent: Intent) {
        val smsId = intent.getLongExtra(NotificationHelper.EXTRA_SMS_ID, -1L)
        if (smsId != -1L) {
            // When user taps an SMS notification, switch to SMS history view
            if (isDashboardViewActive) {
                toggleMainView()
            }
            when (intent.action) {
                NotificationHelper.ACTION_MARK_SAFE -> {
                    viewModel.updateFeedback(smsId, UserFeedback.MARKED_SAFE)
                    Toast.makeText(this, "Marked as Safe", Toast.LENGTH_SHORT).show()
                }
                NotificationHelper.ACTION_MARK_SPAM -> {
                    viewModel.updateFeedback(smsId, UserFeedback.MARKED_SPAM)
                    Toast.makeText(this, "Confirmed as Spam", Toast.LENGTH_SHORT).show()
                }
            }
        } else if (intent.action == Intent.ACTION_SEND && intent.type == "text/plain") {
            // Handle shared suspicious text from WhatsApp / SMS
            val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT) ?: ""
            if (sharedText.isNotBlank()) {
                binding.editTestMessage.setText(sharedText)
                // Forward directly into WebView Dashboard
                val escaped = org.json.JSONObject.quote(sharedText)
                binding.webViewDashboard.post {
                    binding.webViewDashboard.evaluateJavascript(
                        """
                        (function() {
                            const input = document.getElementById('smsInput');
                            if (input) {
                                input.value = $escaped;
                                if (window.App) window.App.navigate('check');
                                if (window.MessageDetector) window.MessageDetector.analyzeMessage();
                            }
                        })();
                        """.trimIndent(),
                        null
                    )
                }
                Toast.makeText(this, "Analyzing shared message for scams...", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupRecyclerView() {
        historyAdapter = SmsHistoryAdapter { entity, feedback ->
            viewModel.updateFeedback(entity.id, feedback)
            val msg = if (feedback == UserFeedback.MARKED_SAFE) "Feedback saved: Marked Safe" else "Feedback saved: Reported Spam"
            Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
        }
        binding.recyclerSmsHistory.layoutManager = LinearLayoutManager(this)
        binding.recyclerSmsHistory.adapter = historyAdapter
    }

    private fun observeViewModel() {
        viewModel.totalCount.observe(this) { count ->
            binding.txtTotalCount.text = (count ?: 0).toString()
        }

        viewModel.spamCount.observe(this) { count ->
            binding.txtSpamCount.text = (count ?: 0).toString()
        }

        viewModel.safeCount.observe(this) { count ->
            binding.txtSafeCount.text = (count ?: 0).toString()
        }

        viewModel.allClassifications.observe(this) { list ->
            historyAdapter.submitList(list)
            if (list.isNullOrEmpty()) {
                binding.txtEmptyHistory.visibility = View.VISIBLE
                binding.recyclerSmsHistory.visibility = View.GONE
            } else {
                binding.txtEmptyHistory.visibility = View.GONE
                binding.recyclerSmsHistory.visibility = View.VISIBLE
            }
        }

        // Offline Model status
        if (viewModel.isModelReady()) {
            binding.txtModelStatusTitle.text = getString(R.string.status_model_active)
            binding.txtModelDetails.text = "Loaded 32,744 TF-IDF N-Gram features + Intercept. Zero-latency offline classification."
            binding.dotModelStatus.backgroundTintList = ContextCompat.getColorStateList(this, R.color.color_safe)
        } else {
            binding.txtModelStatusTitle.text = getString(R.string.status_model_loading)
            binding.dotModelStatus.backgroundTintList = ContextCompat.getColorStateList(this, R.color.accent_saffron)
        }

        viewModel.manualTestResult.observe(this) { result ->
            result?.let {
                val banner = if (it.classification.name == "SPAM") "🚨 SPAM (${it.confidencePercent}% confidence)" else "✅ SAFE (${it.confidencePercent}% confidence)"
                Toast.makeText(this, "Result: $banner\n${it.explanation}", Toast.LENGTH_LONG).show()
                binding.editTestMessage.text.clear()
            }
        }
    }

    private fun setupListeners() {
        binding.btnToggleView.setOnClickListener {
            toggleMainView()
        }

        binding.btnGrantPermission.setOnClickListener {
            requestRequiredPermissions()
        }

        binding.btnClearHistory.setOnClickListener {
            showClearHistoryDialog()
        }

        binding.btnSimulateSpam.setOnClickListener {
            binding.editTestMessage.setText(
                "URGENT: CSPDCL Electricity officer notice. Your power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer at 9876543210 immediately."
            )
        }

        binding.btnRunClassification.setOnClickListener {
            val text = binding.editTestMessage.text.toString().trim()
            if (text.isNotBlank()) {
                viewModel.testManualMessage("Test Simulator", text)
            } else {
                Toast.makeText(this, "Please enter a message to simulate", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun checkPermissions() {
        val hasSms = PermissionHelper.hasReceiveSmsPermission(this)
        updatePermissionUi(hasSms)
    }

    private fun updatePermissionUi(hasSmsPermission: Boolean) {
        if (hasSmsPermission) {
            binding.bannerPermission.backgroundTintList = ContextCompat.getColorStateList(this, R.color.color_safe_bg)
            binding.txtPermissionStatus.text = getString(R.string.permission_granted)
            binding.txtPermissionStatus.setTextColor(ContextCompat.getColor(this, R.color.color_safe))
            binding.btnGrantPermission.visibility = View.GONE
        } else {
            binding.bannerPermission.backgroundTintList = ContextCompat.getColorStateList(this, R.color.accent_saffron_soft)
            binding.txtPermissionStatus.text = getString(R.string.permission_needed)
            binding.txtPermissionStatus.setTextColor(ContextCompat.getColor(this, R.color.accent_saffron))
            binding.btnGrantPermission.visibility = View.VISIBLE
        }
    }

    private fun requestRequiredPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.RECORD_AUDIO
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        requestPermissionLauncher.launch(permissions.toTypedArray())
    }

    private fun showClearHistoryDialog() {
        AlertDialog.Builder(this)
            .setTitle("Clear Detection History")
            .setMessage("Are you sure you want to delete all locally analyzed SMS history? This cannot be undone.")
            .setPositiveButton("Clear All") { _, _ ->
                viewModel.clearHistory()
                Toast.makeText(this, "History cleared", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
}
