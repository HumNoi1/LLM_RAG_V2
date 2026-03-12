export default function DashboardLoading() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Sarabun', sans-serif; background: #f8fafc; }
        
        .dashboard-root { display: flex; min-height: 100vh; }
        
        /* Sidebar Skeleton */
        .sidebar {
          width: 240px; flex-shrink: 0;
          background: #fff;
          border-right: 1px solid #f1f5f9;
          padding: 24px 20px 20px;
        }
        .logo-skeleton {
          display: flex; align-items: center; gap: 12px;
          margin-bottom: 20px;
        }
        .logo-icon-skeleton {
          width: 40px; height: 40px;
          border-radius: 12px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          flex-shrink: 0;
        }
        .logo-text-skeleton {
          width: 80px; height: 16px;
          border-radius: 4px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          margin-bottom: 6px;
        }
        .nav-items-skeleton {
          display: flex; flex-direction: column; gap: 8px;
          margin-bottom: 20px;
        }
        .nav-item-skeleton {
          width: 100%; height: 40px;
          border-radius: 10px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
        }
        
        /* Main Content Skeleton */
        .main {
          margin-left: 240px;
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 32px;
        }
        
        .topbar-skeleton {
          height: 64px;
          background: #fff;
          border-bottom: 1px solid #f1f5f9;
          border-radius: 12px;
          margin-bottom: 32px;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
          margin-bottom: 32px;
        }
        
        .stat-skeleton {
          background: #fff;
          border-radius: 20px;
          border: 1px solid #f1f5f9;
          padding: 24px 28px;
          height: 120px;
        }
        
        .skeleton-line {
          height: 16px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          border-radius: 4px;
          margin-bottom: 12px;
        }
        
        .skeleton-line.short { width: 60%; }
        .skeleton-line.medium { width: 80%; }
        
        .two-col {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }
        
        .card-skeleton {
          background: #fff;
          border-radius: 20px;
          border: 1px solid #f1f5f9;
          overflow: hidden;
        }
        
        .card-header-skeleton {
          padding: 20px 24px 16px;
          border-bottom: 1px solid #f8fafc;
        }
        
        .card-body-skeleton {
          padding: 0;
        }
        
        .skeleton-item {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 24px;
          border-bottom: 1px solid #f8fafc;
        }
        
        .skeleton-item:last-child {
          border-bottom: none;
        }
        
        .skeleton-thumb {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          flex-shrink: 0;
        }
        
        .skeleton-content {
          flex: 1;
        }
        
        .skeleton-text {
          height: 14px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          border-radius: 4px;
          margin-bottom: 6px;
        }
        
        .skeleton-text-small {
          height: 12px;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
          border-radius: 4px;
          width: 80%;
        }
        
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: calc(200% + 200px) 0; }
        }
        
        @media (max-width: 1100px) {
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
          .two-col {
            grid-template-columns: 1fr;
          }
        }
        
        @media (max-width: 768px) {
          .sidebar {
            display: none;
          }
          .main {
            margin-left: 0;
            padding: 20px;
          }
          .stats-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
      `}</style>

      <div className="dashboard-root">
        {/* Sidebar Skeleton */}
        <aside className="sidebar">
          <div className="logo-skeleton">
            <div className="logo-icon-skeleton" />
            <div style={{ flex: 1 }}>
              <div className="logo-text-skeleton" />
              <div className="logo-text-skeleton" style={{ width: '60px' }} />
            </div>
          </div>

          <div className="nav-items-skeleton">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="nav-item-skeleton" />
            ))}
          </div>
        </aside>

        {/* Main Content Skeleton */}
        <div className="main">
          {/* Topbar Skeleton */}
          <div className="topbar-skeleton" />

          {/* Stats Grid Skeleton */}
          <div className="stats-grid">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="stat-skeleton">
                <div className="skeleton-line short" />
                <div className="skeleton-line" style={{ width: '50%' }} />
              </div>
            ))}
          </div>

          {/* Two Column Layout Skeleton */}
          <div className="two-col">
            {/* Recent Exams Card */}
            <div className="card-skeleton">
              <div className="card-header-skeleton">
                <div className="skeleton-line" style={{ width: '40%' }} />
              </div>
              <div className="card-body-skeleton">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="skeleton-item">
                    <div className="skeleton-thumb" />
                    <div className="skeleton-content" style={{ flex: 1 }}>
                      <div className="skeleton-text" />
                      <div className="skeleton-text-small" />
                    </div>
                    <div style={{ width: '60px' }}>
                      <div className="skeleton-text" style={{ width: '100%', marginBottom: '4px' }} />
                      <div className="skeleton-text-small" style={{ width: '60%' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Courses Card */}
            <div className="card-skeleton">
              <div className="card-header-skeleton">
                <div className="skeleton-line" style={{ width: '40%' }} />
              </div>
              <div className="card-body-skeleton">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="skeleton-item">
                    <div className="skeleton-thumb" />
                    <div className="skeleton-content" style={{ flex: 1 }}>
                      <div className="skeleton-text" />
                      <div className="skeleton-text-small" />
                    </div>
                    <div style={{ width: '50px' }}>
                      <div className="skeleton-text" style={{ width: '100%', marginBottom: '4px', height: '18px' }} />
                      <div className="skeleton-text-small" style={{ width: '80%' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
