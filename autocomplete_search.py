from flask import Flask, request, jsonify
from collections import defaultdict
import heapq

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.frequency = 0  # For tracking word popularity

class AutocompleteSearch:
    def __init__(self):
        self.root = TrieNode()
        self.cache = {}  # Hash Map for caching frequent queries
        self.cache_size = 100  # Maximum cache size
        self.cache_queue = []  # For LRU cache eviction

    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.frequency += 1  # Increment frequency for popularity

    def search_prefix(self, prefix, max_suggestions=5):
        # Check cache first
        if prefix in self.cache:
            return self.cache[prefix]

        # Traverse to the prefix node
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        # Collect words with the given prefix
        suggestions = []
        self._collect_words(node, prefix, suggestions, max_suggestions)

        # Cache the result
        if len(self.cache) >= self.cache_size:
            # Remove least recently used item
            oldest_prefix = heapq.heappop(self.cache_queue)[1]
            del self.cache[oldest_prefix]
        self.cache[prefix] = suggestions
        heapq.heappush(self.cache_queue, (-len(suggestions), prefix))

        return suggestions

    def _collect_words(self, node, prefix, suggestions, max_suggestions):
        if len(suggestions) >= max_suggestions:
            return
        if node.is_end:
            suggestions.append((prefix, node.frequency))
        for char, child in node.children.items():
            self._collect_words(child, prefix + char, suggestions, max_suggestions)

# Flask web interface
app = Flask(__name__)
search_engine = AutocompleteSearch()

# Sample dictionary of words
sample_words = [
    "apple", "app", "apricot", "banana", "bat", "ball", 
    "car", "cat", "cake", "dog", "door"
]

# Insert sample words into Trie
for word in sample_words:
    search_engine.insert(word)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Autocomplete Search</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            input { padding: 10px; width: 300px; font-size: 16px; }
            ul { list-style-type: none; padding: 0; }
            li { padding: 8px; cursor: pointer; }
            li:hover { background-color: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>Autocomplete Search Engine</h1>
        <input type="text" id="searchInput" placeholder="Type to search..." onkeyup="fetchSuggestions()">
        <ul id="suggestions"></ul>
        <script>
            async function fetchSuggestions() {
                const query = document.getElementById('searchInput').value;
                if (query.length === 0) {
                    document.getElementById('suggestions').innerHTML = '';
                    return;
                }
                const response = await fetch(`/autocomplete?query=${query}`);
                const suggestions = await response.json();
                const suggestionsList = document.getElementById('suggestions');
                suggestionsList.innerHTML = '';
                suggestions.forEach(suggestion => {
                    const li = document.createElement('li');
                    li.textContent = suggestion[0] + ' (freq: ' + suggestion[1] + ')';
                    li.onclick = () => {
                        document.getElementById('searchInput').value = suggestion[0];
                        suggestionsList.innerHTML = '';
                    };
                    suggestionsList.appendChild(li);
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '')
    suggestions = search_engine.search_prefix(query)
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)