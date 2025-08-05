#include <iostream>
#include <fstream>
#include <unordered_map>
#include <vector>
#include <sstream>
#include <string>
#include <queue>
#include <deque>
#include <limits>
#include <algorithm>
#include <filesystem>
#include <chrono> 
#include <iomanip> 

using namespace std;
namespace fs = filesystem;

unordered_map<int, vector<pair<int, int>>> graph;

struct PerformanceMetrics {
    string timestamp;
    string algorithm;
    int source;
    int target;
    double load_time;
    double algorithm_time;
    int nodes_visited;
    int path_length;
    int graph_nodes;
    int graph_edges;
};

void writeMetricsToCSV(const PerformanceMetrics& metrics) {
    ofstream metricsFile("performance_metrics.csv", ios::app);
    if (metricsFile.is_open()) {
        metricsFile << metrics.timestamp << ","
                    << metrics.algorithm << ","
                    << metrics.source << ","
                    << metrics.target << ","
                    << metrics.load_time << ","
                    << metrics.algorithm_time << ","
                    << metrics.nodes_visited << ","
                    << metrics.path_length << ","
                    << metrics.graph_nodes << ","
                    << metrics.graph_edges << "\n";
        metricsFile.close();
    }
}

void loadGraph(const string& filename) {
    ifstream file(filename);
    string line;
    while (getline(file, line)) {
        stringstream ss(line);
        int from, to, weight;
        char comma;
        ss >> from >> comma >> to >> comma >> weight;
        graph[from].emplace_back(to, weight);
    }
}

void printGraphStats() {
    cout << "Graph loaded with " << graph.size() << " nodes." << endl;
    size_t edge_count = 0;
    for (const auto& [node, edges] : graph) {
        edge_count += edges.size();
    }
    cout << "Total edges: " << edge_count << endl;
}

vector<int> dijkstra(int source, int target, int& nodes_visited) {
    nodes_visited = 0;
    unordered_map<int, int> dist, prev;
    for (const auto& [node, _] : graph) dist[node] = numeric_limits<int>::max();
    dist[source] = 0;
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
    pq.emplace(0, source);

    while (!pq.empty()) {
        auto [cost, u] = pq.top(); pq.pop();
        nodes_visited++;
        if (u == target) break;
        if (cost > dist[u]) continue;
        for (auto [v, w] : graph[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                prev[v] = u;
                pq.emplace(dist[v], v);
            }
        }
    }

    vector<int> path;
    for (int at = target; prev.count(at); at = prev[at]) path.push_back(at);
    if (dist[target] == numeric_limits<int>::max()) return {};
    path.push_back(source);
    reverse(path.begin(), path.end());
    return path;
}

vector<int> dial(int source, int target, int& nodes_visited, int max_weight = 50) {
    nodes_visited = 0;
    unordered_map<int, int> dist, prev;
    for (const auto& [node, _] : graph) dist[node] = numeric_limits<int>::max();
    dist[source] = 0;
    vector<deque<int>> buckets(max_weight * graph.size());
    buckets[0].push_back(source);
    int idx = 0;

    while (true) {
        while (idx < buckets.size() && buckets[idx].empty()) ++idx;
        if (idx == buckets.size()) break;

        int u = buckets[idx].front();
        buckets[idx].pop_front();
        nodes_visited++;

        for (auto [v, w] : graph[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                prev[v] = u;
                buckets[dist[v]].push_back(v);
            }
        }
    }

    vector<int> path;
    for (int at = target; prev.count(at); at = prev[at]) path.push_back(at);
    if (dist[target] == numeric_limits<int>::max()) return {};
    path.push_back(source);
    reverse(path.begin(), path.end());
    return path;
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        cerr << "Usage: " << argv[0] << " <graph.csv> <dijkstra|dial> <source_id> <target_id>\n";
        return 1;
    }

    auto total_start = chrono::high_resolution_clock::now();
    string graph_file = argv[1];
    string algo = argv[2];
    int source = stoi(argv[3]);
    int target = stoi(argv[4]);

    auto load_start = chrono::high_resolution_clock::now();
    loadGraph(graph_file);
    auto load_end = chrono::high_resolution_clock::now();
    double load_time = chrono::duration<double, milli>(load_end - load_start).count();
    
    printGraphStats();
    
    int graph_nodes = graph.size();
    int graph_edges = 0;
    for (const auto& [node, edges] : graph) {
        graph_edges += edges.size();
    }

    if (graph.count(source)) {
        cout << "Source node " << source << " has " << graph[source].size() << " neighbors:\n";
    } else {
        cout << "Source node " << source << " not found in graph.\n";
    }

    if (graph.count(target)) {
        cout << "Target node " << target << " is in graph.\n";
    } else {
        cout << "Target node " << target << " not found in graph.\n";
    }

    vector<int> path;
    int nodes_visited = 0;
    auto algo_start = chrono::high_resolution_clock::now();
    
    if (algo == "dijkstra") {
        path = dijkstra(source, target, nodes_visited);
    } else if (algo == "dial") {
        path = dial(source, target, nodes_visited);
    } else {
        cerr << "Unknown algorithm: " << algo << endl;
        return 1;
    }
    
    auto algo_end = chrono::high_resolution_clock::now();
    double algorithm_time = chrono::duration<double, milli>(algo_end - algo_start).count();

    auto now = chrono::system_clock::now();
    auto in_time_t = chrono::system_clock::to_time_t(now);
    stringstream timestamp;
    timestamp << put_time(localtime(&in_time_t), "%Y-%m-%d %X");

    PerformanceMetrics metrics;
    metrics.timestamp = timestamp.str();
    metrics.algorithm = algo;
    metrics.source = source;
    metrics.target = target;
    metrics.load_time = load_time;
    metrics.algorithm_time = algorithm_time;
    metrics.nodes_visited = nodes_visited;
    metrics.path_length = path.empty() ? -1 : (path.size() - 1);
    metrics.graph_nodes = graph_nodes;
    metrics.graph_edges = graph_edges;

    writeMetricsToCSV(metrics);

    fs::create_directories("../results");
    ofstream out("../results/shortest_path.txt");
    if (!out) {
        cerr << "Failed to open output file: ../results/shortest_path.txt\n";
        return 1;
    }

    if (path.empty()) {
        string msg = "No path found from " + to_string(source) + " to " + to_string(target) + ".\n";
        cout << msg;
        out << msg;
    } else {
        cout << "Path found from " << source << " to " << target << ":\n";
        out  << "Path from " << source << " to " << target << ":\n";

        for (size_t i = 0; i < path.size(); ++i) {
            cout << path[i];
            out  << path[i];
            if (i + 1 < path.size()) {
                cout << " -> ";
                out  << " -> ";
            }
        }

        cout << "\nLength: " << (path.size() - 1) << endl;
        out  << "\nLength: " << (path.size() - 1) << endl;
    }

    auto total_end = chrono::high_resolution_clock::now();
    double total_time = chrono::duration<double, milli>(total_end - total_start).count();
    cout << "Total execution time: " << total_time << " ms" << endl;

    return 0;
}