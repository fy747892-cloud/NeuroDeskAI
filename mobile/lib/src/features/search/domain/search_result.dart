class SearchResult {
  const SearchResult({
    required this.sourceType,
    required this.sourceId,
    required this.title,
    required this.snippet,
    required this.score,
  });

  final String sourceType;
  final String sourceId;
  final String title;
  final String snippet;
  final double score;

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      sourceType: json['source_type'] as String,
      sourceId: json['source_id'] as String,
      title: json['title'] as String,
      snippet: json['snippet'] as String,
      score: (json['score'] as num).toDouble(),
    );
  }
}
