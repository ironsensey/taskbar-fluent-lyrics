// Exercises the production LiveSettings::Apply, SpawnTrackedWorker, and
// Wh_ModSettingsChanged functions extracted by tools/test.py.
#include <cassert>
#include <iostream>
#include <condition_variable>
#include <thread>

static void WaitForTestWorkers() {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    while (g_activeWorkerThreads.load() != 0) {
        assert(std::chrono::steady_clock::now() < deadline);
        std::this_thread::yield();
    }
}
static void TestSettingsLifecycle() {
    struct MockActions {
        std::vector<std::string> trace;
        std::string failAt;
        bool paused = false, producers = true, workers = true;
        bool configurationResult = true;
        int errors = 0, resumes = 0;
        void Phase(const char* phase) {
            trace.push_back(phase);
            if (failAt == phase) throw std::runtime_error(phase);
        }
        void Pause() { Phase("pause"); paused = true; }
        void StopProducers() { assert(paused); Phase("stop"); producers = false; }
        void DrainWorkers() { assert(!producers); Phase("drain"); workers = false; }
        bool ReconfigureOnUi() {
            assert(paused && !producers && !workers);
            Phase("apply");
            return configurationResult;
        }
        void Resume() { ++resumes; paused = false; producers = true; Phase("resume"); }
        void ReportFailure() noexcept { ++errors; }
    };
    MockActions success;
    assert(LiveSettings::Apply(success));
    assert((success.trace == std::vector<std::string>{"pause", "stop", "drain", "apply", "resume"}));
    assert(!success.paused && success.resumes == 1);
    for (const auto* failure : {"pause", "stop", "drain", "apply", "resume"}) {
        MockActions actions;
        actions.failAt = failure;
        assert(!LiveSettings::Apply(actions));
        assert(actions.errors == 1 && !actions.paused);
        assert(actions.resumes == (actions.failAt == "pause" ? 0 : 1));
    }
    MockActions rejected;
    rejected.configurationResult = false;
    assert(!LiveSettings::Apply(rejected));
    assert(rejected.resumes == 1 && !rejected.paused && rejected.errors == 0);

    for (int iteration = 0; iteration < 1000; ++iteration) {
        BOOL reload = TRUE;
        testLiveSettingsSuccess = iteration % 7 != 0;
        const BOOL result = Wh_ModSettingsChanged(&reload);
        assert(reload == FALSE); // The old forced-unload callback fails here.
        assert(result == (testLiveSettingsSuccess ? TRUE : FALSE));
    }
    testLiveSettingsSuccess = true;
    assert(Wh_ModSettingsChanged(nullptr) == TRUE);

    struct RunningActions {
        std::mutex mutex;
        std::condition_variable condition;
        bool releaseJobs = false;
        std::string config = "old";
        std::atomic<int> forbiddenStarts{0};
        void StartReaders() {
            for (int i = 0; i < 2; ++i) SpawnTrackedWorker([this] {
                const auto snapshot = config;
                std::unique_lock<std::mutex> lock(mutex);
                condition.wait(lock, [this] { return releaseJobs; });
                assert(config == snapshot); // Settings cannot mutate under an old job.
            });
        }
        void Pause() {
            std::lock_guard<std::mutex> lock(g_workerAdmissionMutex);
            g_applyingSettings = true;
        }
        void StopProducers() {
            // A concurrent event during a settings save must not admit new work.
            SpawnTrackedWorker([this] { ++forbiddenStarts; });
            { std::lock_guard<std::mutex> lock(mutex); releaseJobs = true; }
            condition.notify_all();
        }
        void DrainWorkers() { WaitForTestWorkers(); }
        bool ReconfigureOnUi() { assert(g_activeWorkerThreads == 0); config = "new"; return true; }
        void Resume() {
            std::lock_guard<std::mutex> lock(g_workerAdmissionMutex);
            g_applyingSettings = false;
        }
        void ReportFailure() noexcept { assert(false); }
    };
    for (int iteration = 0; iteration < 100; ++iteration) {
        RunningActions actions;
        actions.StartReaders();
        assert(LiveSettings::Apply(actions));
        assert(actions.forbiddenStarts == 0 && actions.config == "new");
        assert(g_activeWorkerThreads == 0 && !g_applyingSettings);
    }
    struct CapturedResource {
        std::atomic<bool>& destroyed;
        explicit CapturedResource(std::atomic<bool>& result) : destroyed(result) {}
        ~CapturedResource() {
            assert(g_activeWorkerThreads.load() > 0);
            destroyed = true;
        }
    };
    std::atomic<bool> captureDestroyed{false};
    SpawnTrackedWorker([resource = std::make_unique<CapturedResource>(captureDestroyed)] { assert(resource); });
    WaitForTestWorkers();
    assert(captureDestroyed);
    g_unloading = true;
    std::atomic<int> forbiddenOnUnload{0};
    SpawnTrackedWorker([&] { ++forbiddenOnUnload; });
    assert(forbiddenOnUnload == 0 && g_activeWorkerThreads == 0);
    g_unloading = false;
    std::cout << "PASS: settings lifecycle success/failure recovery, 1,000 no-reload saves and 100 active-worker drain cycles\n";
}
