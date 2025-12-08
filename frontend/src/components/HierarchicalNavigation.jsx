import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

/**
 * HierarchicalNavigation Component
 * 
 * Breadcrumb navigation component for hierarchical structure:
 * Survey → Platform → Respondent → Session
 */
const HierarchicalNavigation = ({ 
  surveyId, 
  platformId, 
  respondentId, 
  sessionId,
  surveyName,
  platformName,
  respondentName,
  sessionName
}) => {
  const breadcrumbs = [];

  // Home
  breadcrumbs.push({
    label: 'Home',
    path: '/',
    icon: <Home className="w-4 h-4" />
  });

  // Survey
  if (surveyId) {
    breadcrumbs.push({
      label: surveyName || `Survey: ${surveyId}`,
      path: `/surveys/${surveyId}`
    });
  }

  // Platform
  if (surveyId && platformId) {
    breadcrumbs.push({
      label: platformName || `Platform: ${platformId}`,
      path: `/surveys/${surveyId}/platforms/${platformId}`
    });
  }

  // Respondent
  if (surveyId && platformId && respondentId) {
    breadcrumbs.push({
      label: respondentName || `Respondent: ${respondentId}`,
      path: `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}`
    });
  }

  // Session
  if (surveyId && platformId && respondentId && sessionId) {
    breadcrumbs.push({
      label: sessionName || `Session: ${sessionId.substring(0, 8)}...`,
      path: `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}`
    });
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={index}>
          {index > 0 && <ChevronRight className="w-4 h-4 text-gray-400" />}
          {index === breadcrumbs.length - 1 ? (
            <span className="text-gray-900 font-medium">{crumb.icon || crumb.label}</span>
          ) : (
            <Link 
              to={crumb.path} 
              className="hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              {crumb.icon}
              <span>{crumb.label}</span>
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default HierarchicalNavigation;

