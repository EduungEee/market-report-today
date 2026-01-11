import { NewsArticle } from "@/lib/api/reports";

interface NewsListProps {
  articles: NewsArticle[];
}

/**
 * 뉴스 기사 리스트 컴포넌트
 */
export function NewsList({ articles }: NewsListProps) {
  if (articles.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-600 dark:text-slate-400">뉴스 기사가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {articles.map((article) => (
        <article
          key={article.id}
          className="p-4 border rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-slate-900"
        >
          <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-slate-50">{article.title}</h3>
          {article.content && (
            <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-3">{article.content}</p>
          )}
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-500">
            <div className="flex gap-4">
              {article.source && <span>{article.source}</span>}
              {article.published_at && <span>{new Date(article.published_at).toLocaleDateString("ko-KR")}</span>}
            </div>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                원문 보기 →
              </a>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
