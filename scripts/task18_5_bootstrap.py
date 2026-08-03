#!/usr/bin/env python3
from pathlib import Path
from textwrap import dedent


def write(path: str, content: str, executable: bool = False) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dedent(content).lstrip())
    if executable:
        target.chmod(0o755)


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    content = target.read_text()
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    target.write_text(content.replace(old, new))


kotlin_path = "crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt"
replace_once(
    kotlin_path,
    "import java.util.concurrent.Callable\nimport java.util.concurrent.ConcurrentHashMap\n",
    "import java.util.concurrent.Callable\nimport java.util.concurrent.CompletableFuture\nimport java.util.concurrent.ConcurrentHashMap\n",
    "CompletableFuture import",
)
replace_once(
    kotlin_path,
    """class SearchOperation internal constructor(
    private val future: Future<SearchResult>,
    private val cancellation: AtomicLong,
) {
""",
    """class SearchOperation internal constructor(
    private val future: Future<SearchResult>,
    private val cancellation: AtomicLong,
    private val executionThread: CompletableFuture<String>,
) {
""",
    "SearchOperation constructor",
)
replace_once(
    kotlin_path,
    """    fun isDone(): Boolean = future.isDone

    fun await(): SearchResult = try {
""",
    """    fun isDone(): Boolean = future.isDone

    /** Test-harness diagnostic proving where the synchronous JNI call executes. */
    internal fun executionThreadName(timeout: Long, unit: TimeUnit): String =
        executionThread.get(timeout, unit)

    fun await(): SearchResult = try {
""",
    "SearchOperation execution diagnostic",
)
replace_once(
    kotlin_path,
    """        activeCancellation.set(cancellationHandle)
        val operationCancellation = AtomicLong(cancellationHandle)

        val future = try {
""",
    """        activeCancellation.set(cancellationHandle)
        val operationCancellation = AtomicLong(cancellationHandle)
        val executionThread = CompletableFuture<String>()

        val future = try {
""",
    "Search execution future",
)
replace_once(
    kotlin_path,
    """            executor.submit(Callable {
                try {
                    lifecycleLock.read {
""",
    """            executor.submit(Callable {
                executionThread.complete(Thread.currentThread().name)
                try {
                    lifecycleLock.read {
""",
    "Search worker recording",
)
replace_once(
    kotlin_path,
    "        return SearchOperation(future, operationCancellation)\n",
    "        return SearchOperation(future, operationCancellation, executionThread)\n",
    "SearchOperation return",
)

write(
    "scripts/build_android_jni.sh",
    r'''
    #!/usr/bin/env bash
    set -euo pipefail

    ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "${ROOT_DIR}"

    TARGET="${ANDROID_RUST_TARGET:-aarch64-linux-android}"
    API_LEVEL="${ANDROID_API_LEVEL:-24}"
    NDK_HOME="${ANDROID_NDK_HOME:-${ANDROID_NDK_ROOT:-}}"
    HOST_TAG="${ANDROID_NDK_HOST_TAG:-linux-x86_64}"

    if [[ -z "${NDK_HOME}" ]]; then
      echo "ANDROID_NDK_HOME or ANDROID_NDK_ROOT must name an installed Android NDK." >&2
      exit 2
    fi

    case "${TARGET}" in
      aarch64-linux-android)
        LINKER_TRIPLE="aarch64-linux-android"
        CARGO_PREFIX="AARCH64_LINUX_ANDROID"
        CC_VARIABLE="CC_aarch64_linux_android"
        AR_VARIABLE="AR_aarch64_linux_android"
        ;;
      x86_64-linux-android)
        LINKER_TRIPLE="x86_64-linux-android"
        CARGO_PREFIX="X86_64_LINUX_ANDROID"
        CC_VARIABLE="CC_x86_64_linux_android"
        AR_VARIABLE="AR_x86_64_linux_android"
        ;;
      *)
        echo "Unsupported Android Rust target: ${TARGET}" >&2
        echo "Supported targets: aarch64-linux-android, x86_64-linux-android" >&2
        exit 2
        ;;
    esac

    TOOLCHAIN="${NDK_HOME}/toolchains/llvm/prebuilt/${HOST_TAG}"
    LINKER="${TOOLCHAIN}/bin/${LINKER_TRIPLE}${API_LEVEL}-clang"
    AR="${TOOLCHAIN}/bin/llvm-ar"

    if [[ ! -x "${LINKER}" ]]; then
      echo "Android linker not found: ${LINKER}" >&2
      exit 2
    fi
    if [[ ! -x "${AR}" ]]; then
      echo "Android LLVM archiver not found: ${AR}" >&2
      exit 2
    fi

    rustup target add "${TARGET}"

    export "CARGO_TARGET_${CARGO_PREFIX}_LINKER=${LINKER}"
    export "CARGO_TARGET_${CARGO_PREFIX}_AR=${AR}"
    export "${CC_VARIABLE}=${LINKER}"
    export "${AR_VARIABLE}=${AR}"

    cargo build --locked -p chess-jni --target "${TARGET}" --release

    LIBRARY="target/${TARGET}/release/libchess_jni.so"
    if [[ ! -s "${LIBRARY}" ]]; then
      echo "Expected nonempty Android JNI library was not produced: ${LIBRARY}" >&2
      exit 1
    fi

    printf '%s\n' "${LIBRARY}"
    ''',
    executable=True,
)

write(
    "scripts/prepare_android_harness_jni.sh",
    r'''
    #!/usr/bin/env bash
    set -euo pipefail

    ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    OUTPUT_ROOT="${ANDROID_HARNESS_JNI_LIBS_DIR:-${ROOT_DIR}/android-harness/android-smoke/src/main/jniLibs}"

    rm -rf "${OUTPUT_ROOT}"
    mkdir -p "${OUTPUT_ROOT}"

    build_and_copy() {
      local target="$1"
      local abi="$2"
      ANDROID_RUST_TARGET="${target}" "${ROOT_DIR}/scripts/build_android_jni.sh"
      local source="${ROOT_DIR}/target/${target}/release/libchess_jni.so"
      local destination="${OUTPUT_ROOT}/${abi}/libchess_jni.so"
      install -D -m 0755 "${source}" "${destination}"
      test -s "${destination}"
      printf '%s\n' "${destination}"
    }

    build_and_copy aarch64-linux-android arm64-v8a
    build_and_copy x86_64-linux-android x86_64
    ''',
    executable=True,
)

write(
    "android-harness/settings.gradle.kts",
    r'''
    pluginManagement {
        repositories {
            google()
            mavenCentral()
            gradlePluginPortal()
        }
    }

    dependencyResolutionManagement {
        repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
        repositories {
            google()
            mavenCentral()
        }
    }

    rootProject.name = "ChessEngineAndroidHarness"
    include(":host-jvm")
    include(":android-smoke")
    ''',
)

write(
    "android-harness/build.gradle.kts",
    r'''
    plugins {
        kotlin("jvm") version "2.0.21" apply false
        id("com.android.library") version "8.7.3" apply false
        id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    }
    ''',
)

write(
    "android-harness/gradle.properties",
    r'''
    android.useAndroidX=true
    android.nonTransitiveRClass=true
    kotlin.code.style=official
    org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
    ''',
)

write(
    "android-harness/.gitignore",
    r'''
    .gradle/
    local.properties
    **/build/
    android-smoke/src/main/jniLibs/
    ''',
)

write(
    "android-harness/host-jvm/build.gradle.kts",
    r'''
    plugins {
        kotlin("jvm")
    }

    kotlin {
        jvmToolchain(17)
    }

    sourceSets {
        main {
            kotlin.srcDir("../../crates/chess-jni/kotlin/src/main/kotlin")
        }
    }

    dependencies {
        testImplementation(kotlin("test-junit5"))
        testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    }

    tasks.test {
        useJUnitPlatform()
        val nativeDirectory = rootProject.file("../target/release").absolutePath
        jvmArgs("-Djava.library.path=$nativeDirectory")
        testLogging {
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ''',
)

write(
    "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/ChessEngineHostJvmTest.kt",
    r'''
    package com.ekkus93.chessengine

    import java.util.concurrent.TimeUnit
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertFalse
    import org.junit.jupiter.api.Assertions.assertNotEquals
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Assertions.assertThrows
    import org.junit.jupiter.api.Assertions.assertTrue
    import org.junit.jupiter.api.Test
    import org.junit.jupiter.api.Timeout

    class ChessEngineHostJvmTest {
        @Test
        @Timeout(30)
        fun publicLifecycleUsesTheRealNativeLibrary() {
            val engine = ChessEngine.create()
            val startingFen = engine.fen()
            val legalMoves = engine.legalMoves()

            assertEquals("0.1.0", engine.version)
            assertTrue(startingFen.endsWith(" w KQkq - 0 1"))
            assertEquals(20, legalMoves.size)
            assertTrue("e2e4" in legalMoves)
            assertEquals(GameStatusKind.ONGOING, engine.gameStatus().kind)
            assertNotEquals(0u, engine.weightIdentity().schemaVersion)

            val operation = engine.search(SearchRequest(depth = 2))
            assertEquals(
                "chess-engine-search",
                operation.executionThreadName(5, TimeUnit.SECONDS),
            )
            val result = operation.await()
            assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
            assertEquals(2, result.completedDepth)
            assertNotNull(result.bestMove)
            assertTrue(result.bestMove in legalMoves)
            assertTrue(result.nodes > 0uL)

            engine.playMove("e2e4")
            assertTrue(engine.fen().contains(" b "))
            engine.resetPosition()
            assertEquals(startingFen, engine.fen())

            engine.close()
            engine.close()
            assertThrows(IllegalStateException::class.java) { engine.fen() }
        }

        @Test
        @Timeout(30)
        fun invalidFenMapsToTypedExceptionAndPreservesState() {
            ChessEngine.create().use { engine ->
                val before = engine.fen()
                val error = assertThrows(ChessEngineException::class.java) {
                    engine.setPosition("not a fen")
                }
                assertEquals(ChessEngineErrorCode.INVALID_FEN, error.code)
                assertEquals(before, engine.fen())
            }
        }

        @Test
        @Timeout(30)
        fun infiniteSearchStopsThroughTheNativeCancellationToken() {
            ChessEngine.create().use { engine ->
                val legalMoves = engine.legalMoves()
                val operation = engine.search(SearchRequest(infinite = true))
                val worker = operation.executionThreadName(5, TimeUnit.SECONDS)
                assertNotEquals(Thread.currentThread().name, worker)
                assertEquals("chess-engine-search", worker)
                assertTrue(operation.cancel())

                val result = operation.await()
                assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
                assertTrue(result.bestMove in legalMoves)
                assertFalse(operation.cancel())
            }
        }

        @Test
        @Timeout(60)
        fun repeatedCreateSearchStopDestroyIsStable() {
            repeat(24) { iteration ->
                ChessEngine.create().use { engine ->
                    val operation = if (iteration % 2 == 0) {
                        engine.search(SearchRequest(depth = 1))
                    } else {
                        engine.search(SearchRequest(infinite = true)).also {
                            it.executionThreadName(5, TimeUnit.SECONDS)
                            assertTrue(it.cancel())
                        }
                    }
                    val result = operation.await()
                    if (iteration % 2 == 0) {
                        assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                    } else {
                        assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
                    }
                    assertTrue(result.bestMove in engine.legalMoves())
                }
            }
        }
    }
    ''',
)

write(
    "android-harness/android-smoke/build.gradle.kts",
    r'''
    plugins {
        id("com.android.library")
        id("org.jetbrains.kotlin.android")
    }

    android {
        namespace = "com.ekkus93.chessengine.harness"
        compileSdk = 35

        defaultConfig {
            minSdk = 24
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }

        sourceSets {
            getByName("main") {
                java.srcDir("../../crates/chess-jni/kotlin/src/main/kotlin")
                jniLibs.srcDir("src/main/jniLibs")
            }
        }

        buildFeatures {
            buildConfig = false
        }

        packaging {
            jniLibs {
                useLegacyPackaging = false
            }
        }

        testOptions {
            animationsDisabled = true
        }
    }

    kotlin {
        jvmToolchain(17)
    }

    dependencies {
        implementation("androidx.annotation:annotation:1.9.1")
        androidTestImplementation("androidx.test.ext:junit:1.2.1")
        androidTestImplementation("androidx.test:runner:1.6.2")
        androidTestImplementation("junit:junit:4.13.2")
    }
    ''',
)

write(
    "android-harness/android-smoke/src/main/AndroidManifest.xml",
    r'''
    <?xml version="1.0" encoding="utf-8"?>
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" />
    ''',
)

write(
    "android-harness/android-smoke/src/main/kotlin/com/ekkus93/chessengine/harness/ChessEngineSampleController.kt",
    r'''
    package com.ekkus93.chessengine.harness

    import androidx.annotation.MainThread
    import com.ekkus93.chessengine.ChessEngine
    import com.ekkus93.chessengine.SearchOperation
    import com.ekkus93.chessengine.SearchRequest
    import java.io.Closeable

    /** Minimal UI-facing integration that delegates all search work to [ChessEngine]. */
    class ChessEngineSampleController private constructor(
        private val engine: ChessEngine,
    ) : Closeable {
        @MainThread
        fun startDepthSearch(depth: Int): SearchOperation =
            engine.search(SearchRequest(depth = depth))

        fun legalMoves(): List<String> = engine.legalMoves()

        override fun close() = engine.close()

        companion object {
            fun create(): ChessEngineSampleController =
                ChessEngineSampleController(ChessEngine.create())
        }
    }
    ''',
)

write(
    "android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt",
    r'''
    package com.ekkus93.chessengine.harness

    import android.os.Looper
    import androidx.test.ext.junit.runners.AndroidJUnit4
    import androidx.test.platform.app.InstrumentationRegistry
    import com.ekkus93.chessengine.ChessEngine
    import com.ekkus93.chessengine.GameStatusKind
    import com.ekkus93.chessengine.SearchOperation
    import com.ekkus93.chessengine.SearchRequest
    import com.ekkus93.chessengine.SearchTerminationKind
    import java.util.concurrent.TimeUnit
    import java.util.concurrent.atomic.AtomicReference
    import org.junit.Assert.assertEquals
    import org.junit.Assert.assertNotEquals
    import org.junit.Assert.assertSame
    import org.junit.Assert.assertTrue
    import org.junit.Test
    import org.junit.runner.RunWith

    @RunWith(AndroidJUnit4::class)
    class ChessEngineInstrumentedTest {
        @Test(timeout = 60_000L)
        fun realJniLifecycleRunsOnTheEmulator() {
            ChessEngine.create().use { engine ->
                val startingFen = engine.fen()
                val legalMoves = engine.legalMoves()
                assertEquals(20, legalMoves.size)
                assertTrue("e2e4" in legalMoves)
                assertEquals(GameStatusKind.ONGOING, engine.gameStatus().kind)

                val result = engine.search(SearchRequest(depth = 2)).await()
                assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                assertEquals(2, result.completedDepth)
                assertTrue(result.bestMove in legalMoves)

                engine.playMove("e2e4")
                assertTrue(engine.fen().contains(" b "))
                engine.resetPosition()
                assertEquals(startingFen, engine.fen())
            }
        }

        @Test(timeout = 60_000L)
        fun sampleMainThreadEntrySchedulesNativeSearchOnTheWorker() {
            val controller = ChessEngineSampleController.create()
            try {
                val operation = AtomicReference<SearchOperation>()
                val instrumentation = InstrumentationRegistry.getInstrumentation()
                instrumentation.runOnMainSync {
                    assertSame(Looper.getMainLooper(), Looper.myLooper())
                    operation.set(controller.startDepthSearch(2))
                }

                val workerName = operation.get().executionThreadName(5, TimeUnit.SECONDS)
                assertEquals("chess-engine-search", workerName)
                assertNotEquals(Looper.getMainLooper().thread.name, workerName)

                val result = operation.get().await()
                assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                assertTrue(result.bestMove in controller.legalMoves())
            } finally {
                controller.close()
            }
        }

        @Test(timeout = 120_000L)
        fun repeatedCreateSearchStopDestroyIsStableOnAndroid() {
            repeat(16) { iteration ->
                ChessEngine.create().use { engine ->
                    val operation = if (iteration % 2 == 0) {
                        engine.search(SearchRequest(depth = 1))
                    } else {
                        engine.search(SearchRequest(infinite = true)).also {
                            assertEquals(
                                "chess-engine-search",
                                it.executionThreadName(5, TimeUnit.SECONDS),
                            )
                            assertTrue(it.cancel())
                        }
                    }

                    val result = operation.await()
                    if (iteration % 2 == 0) {
                        assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                    } else {
                        assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
                    }
                    assertTrue(result.bestMove in engine.legalMoves())
                }
            }
        }
    }
    ''',
)

write(
    ".github/workflows/android.yml",
    r'''
    name: Android JNI

    on:
      push:
        branches:
          - rust-engine
      pull_request:
        branches:
          - rust-engine
      workflow_dispatch:

    permissions:
      contents: read

    concurrency:
      group: android-jni-${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true

    jobs:
      host-jvm:
        name: Host JVM JNI contract
        runs-on: ubuntu-24.04
        timeout-minutes: 30
        steps:
          - uses: actions/checkout@v4

          - name: Install Rust toolchain
            uses: dtolnay/rust-toolchain@stable

          - name: Install Java 17
            uses: actions/setup-java@v4
            with:
              distribution: temurin
              java-version: "17"

          - name: Install Gradle 8.9
            uses: gradle/actions/setup-gradle@v4
            with:
              gradle-version: "8.9"

          - name: Build host JNI library
            run: cargo build --locked -p chess-jni --release

          - name: Run host JVM contract tests
            run: >-
              gradle -p android-harness :host-jvm:test
              --no-daemon --stacktrace --console=plain

      android-emulator:
        name: Android API 35 JNI smoke
        runs-on: ubuntu-24.04
        timeout-minutes: 45
        steps:
          - uses: actions/checkout@v4

          - name: Install Rust toolchain
            uses: dtolnay/rust-toolchain@stable

          - name: Install Java 17
            uses: actions/setup-java@v4
            with:
              distribution: temurin
              java-version: "17"

          - name: Install Gradle 8.9
            uses: gradle/actions/setup-gradle@v4
            with:
              gradle-version: "8.9"

          - name: Resolve hosted Android NDK
            id: ndk
            shell: bash
            run: |
              set -euo pipefail
              NDK_HOME="${ANDROID_NDK_LATEST_HOME:-}"
              if [[ -z "${NDK_HOME}" || ! -d "${NDK_HOME}" ]]; then
                NDK_HOME="$(find "${ANDROID_SDK_ROOT}/ndk" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)"
              fi
              test -d "${NDK_HOME}"
              echo "home=${NDK_HOME}" >> "${GITHUB_OUTPUT}"
              "${NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/bin/clang" --version

          - name: Build and stage ARM64 and x86_64 JNI libraries
            env:
              ANDROID_NDK_HOME: ${{ steps.ndk.outputs.home }}
              ANDROID_API_LEVEL: "24"
            run: bash scripts/prepare_android_harness_jni.sh

          - name: Verify native artifacts
            shell: bash
            run: |
              set -euo pipefail
              ARM64=android-harness/android-smoke/src/main/jniLibs/arm64-v8a/libchess_jni.so
              X64=android-harness/android-smoke/src/main/jniLibs/x86_64/libchess_jni.so
              test -s "${ARM64}"
              test -s "${X64}"
              file "${ARM64}" | tee /tmp/chess-arm64.txt
              file "${X64}" | tee /tmp/chess-x64.txt
              grep -F 'ARM aarch64' /tmp/chess-arm64.txt
              grep -F 'x86-64' /tmp/chess-x64.txt
              readelf -Ws "${ARM64}" | grep -F 'Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeSearch'
              readelf -Ws "${X64}" | grep -F 'Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeSearch'

          - name: Compile Android library and test APK
            run: >-
              gradle -p android-harness
              :android-smoke:assembleDebug
              :android-smoke:assembleDebugAndroidTest
              --no-daemon --stacktrace --console=plain

          - name: Enable KVM
            shell: bash
            run: |
              echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' \
                | sudo tee /etc/udev/rules.d/99-kvm4all.rules
              sudo udevadm control --reload-rules
              sudo udevadm trigger --name-match=kvm

          - name: Run instrumented JNI lifecycle
            uses: reactivecircus/android-emulator-runner@v2
            with:
              api-level: 35
              arch: x86_64
              target: google_apis
              profile: pixel_2
              disable-animations: true
              emulator-options: >-
                -no-snapshot -no-window -gpu swiftshader_indirect
                -noaudio -no-boot-anim -camera-back none
              script: >-
                gradle -p android-harness
                :android-smoke:connectedDebugAndroidTest
                --no-daemon --stacktrace --console=plain
    ''',
)

write(
    "docs/RUST_ANDROID_TEST_HARNESS.md",
    r'''
    # Android/JVM JNI test harness

    Task 18.5 provides executable JVM and Android coverage for the Task 18.4
    Kotlin/JNI adapter. Both Gradle modules compile the exact production wrapper
    at `crates/chess-jni/kotlin/src/main/kotlin`; no copied or test-specific
    engine implementation exists.

    ## Layout

    - `android-harness/host-jvm` runs the public Kotlin API against the host
      `target/release/libchess_jni.so`.
    - `android-harness/android-smoke` packages the same wrapper and generated
      Android JNI libraries into a minimal Android library and test APK.
    - `scripts/build_android_jni.sh` supports the pinned
      `aarch64-linux-android` and `x86_64-linux-android` Rust targets.
    - `scripts/prepare_android_harness_jni.sh` stages both outputs under the
      Android module's ignored `jniLibs` tree.
    - `.github/workflows/android.yml` is the permanent read-only host/JVM,
      cross-build, APK-build, and emulator gate.

    The Gradle build is pinned to Gradle 8.9, Android Gradle Plugin 8.7.3,
    Kotlin 2.0.21, Java 17, compile SDK 35, and minimum Android API 24.

    ## Host JVM contract

    Build the host JNI library and run the JVM tests from the repository root:

    ```bash
    cargo build --locked -p chess-jni --release
    gradle -p android-harness :host-jvm:test \
      --no-daemon --stacktrace --console=plain
    ```

    The host suite uses the real shared library and covers:

    - construction, version, FEN, legal moves, status, weight identity, search,
      move application, reset, idempotent close, and post-close rejection;
    - typed invalid-FEN exception mapping with state preservation;
    - active infinite-search cancellation through the native stop token; and
    - twenty-four repeated create/search-or-stop/destroy lifecycles.

    ## Android native libraries

    Set an installed Android NDK and stage both supported ABIs:

    ```bash
    export ANDROID_NDK_HOME=/path/to/android-ndk
    export ANDROID_API_LEVEL=24
    bash scripts/prepare_android_harness_jni.sh
    ```

    This produces ignored local artifacts:

    ```text
    android-harness/android-smoke/src/main/jniLibs/arm64-v8a/libchess_jni.so
    android-harness/android-smoke/src/main/jniLibs/x86_64/libchess_jni.so
    ```

    Build the library and instrumentation APKs with:

    ```bash
    gradle -p android-harness \
      :android-smoke:assembleDebug \
      :android-smoke:assembleDebugAndroidTest \
      --no-daemon --stacktrace --console=plain
    ```

    ## Emulator contract

    The permanent workflow boots an Android API-35 x86_64 Google APIs emulator
    and runs:

    ```bash
    gradle -p android-harness \
      :android-smoke:connectedDebugAndroidTest \
      --no-daemon --stacktrace --console=plain
    ```

    Instrumentation coverage performs a real create, FEN/legal/status query,
    fixed-depth search, move, reset, and destroy lifecycle. It also runs sixteen
    alternating fixed-depth and infinite-search cancellation lifecycles.

    `ChessEngineSampleController.startDepthSearch` is deliberately invoked from
    the Android main thread. The operation records the thread that immediately
    enters the synchronous JNI search call; the test requires the deterministic
    `chess-engine-search` worker name and rejects the Android main-loop thread.
    The diagnostic is internal to the Kotlin module and does not alter the native
    request or result format.

    ## Ownership and generated-artifact policy

    Explicit `ChessEngine.close` remains authoritative and is exercised in every
    successful test path. JNI libraries and Gradle build directories are ignored
    generated artifacts and are never committed. The workflow has only
    `contents: read`; it cannot rewrite source or trackers.

    Task 18.5 evidence and the overall Task 18 gate remain open until the exact
    implementation head passes both permanent workflow jobs.
    ''',
)

required = [
    "android-harness/settings.gradle.kts",
    "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/ChessEngineHostJvmTest.kt",
    "android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt",
    ".github/workflows/android.yml",
    "docs/RUST_ANDROID_TEST_HARNESS.md",
]
for item in required:
    if not Path(item).is_file():
        raise SystemExit(f"missing generated Task 18.5 asset: {item}")
