import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, TrendingUp, AlertCircle, Target, MapPin, Lightbulb, ArrowRight } from 'lucide-react';
import BusinessTypeSelector from '../components/BusinessTypeSelector';
import { apiService, KPIData, Strategy } from '../services/api';


export default function Dashboard() {
  const navigate = useNavigate();
  const [selectedBusinessType, setSelectedBusinessType] = useState('showroom');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [kpiData, setKPIData] = useState<KPIData | null>(null);

  useEffect(() => {
    if (selectedBusinessType) {
      loadDashboardData();
    }
  }, [selectedBusinessType]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [strategyData, kpiDataResult] = await Promise.all([
        apiService.getStrategy(selectedBusinessType, 'default'),
        apiService.getKPIData(selectedBusinessType),
      ]);
      setStrategy(strategyData);
      setKPIData(kpiDataResult);
    } catch (err) {
      setError('Unable to load dashboard data. Please ensure backend is running.');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Select Your Business Type</h2>
        <BusinessTypeSelector
          selectedType={selectedBusinessType}
          onSelectType={setSelectedBusinessType}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Connection Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          <div className="bg-gradient-to-br from-blue-600 to-green-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center space-x-3 mb-4">
              <Lightbulb className="w-6 h-6" />
              <h2 className="text-2xl font-bold">AI-Generated Strategy</h2>
            </div>
            {strategy ? (
              <div className="space-y-3">
                <h3 className="text-xl font-semibold">{strategy.title}</h3>
                <p className="text-blue-50">{strategy.description}</p>
                <div className="bg-white/10 rounded-lg p-4 mt-4">
                  <h4 className="font-semibold mb-2">Key Recommendations:</h4>
                  <ul className="space-y-2">
                    {strategy.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-green-300">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-blue-50">Connect to backend to view AI-generated strategies</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6 transform transition-all hover:scale-105">
              <div className="flex items-center justify-between mb-4">
                <Target className="w-8 h-8 text-blue-600" />
                <span className="text-3xl font-bold text-blue-600">
                  {kpiData?.growthScore || '--'}
                </span>
              </div>
              <h3 className="text-gray-600 font-medium">Growth Score</h3>
              <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-1000"
                  style={{ width: `${kpiData?.growthScore || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 transform transition-all hover:scale-105">
              <div className="flex items-center justify-between mb-4">
                <TrendingUp className="w-8 h-8 text-green-600" />
                <span className="text-3xl font-bold text-green-600">
                  {kpiData?.demandLevel || '--'}
                </span>
              </div>
              <h3 className="text-gray-600 font-medium">Demand Level</h3>
              <p className="text-sm text-gray-500 mt-2">Market demand indicator</p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 transform transition-all hover:scale-105">
              <div className="flex items-center justify-between mb-4">
                <AlertCircle className="w-8 h-8 text-orange-600" />
                <span className="text-3xl font-bold text-orange-600">
                  {kpiData?.riskLevel || '--'}
                </span>
              </div>
              <h3 className="text-gray-600 font-medium">Risk Level</h3>
              <p className="text-sm text-gray-500 mt-2">Business risk assessment</p>
            </div>
          </div>

          {kpiData?.insight && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <h3 className="text-lg font-bold text-blue-900 mb-2">Key Insight</h3>
              <p className="text-blue-800">{kpiData.insight}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-blue-100 hover:border-blue-300 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <MessageCircle className="w-8 h-8 text-blue-600" />
                  <h3 className="text-xl font-bold text-gray-800">AI Business Assistant</h3>
                </div>
                <button
                  onClick={() => navigate('/location')}
                  className="bg-gradient-to-r from-blue-600 to-green-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all flex items-center space-x-2"
                >
                  <span>Open Chat</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
              <p className="text-gray-600">
                Get personalized business advice and answers to your questions from our AI-powered assistant.
              </p>
              <div className="mt-4 bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-500 italic">
                  "Ask me about inventory management, pricing strategies, customer acquisition, and more..."
                </p>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-green-100 hover:border-green-300 transition-all">
              <div className="flex items-center space-x-3 mb-4">
                <MapPin className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-gray-800">Location Overview</h3>
              </div>
              <p className="text-gray-600 mb-4">
                View strategic business locations and market insights for your selected area.
              </p>
              <button
                onClick={() => navigate('/location')}
                className="w-full bg-gradient-to-r from-green-600 to-blue-600 text-white px-4 py-3 rounded-lg hover:shadow-lg transition-all flex items-center justify-center space-x-2"
              >
                <span>View Map</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
