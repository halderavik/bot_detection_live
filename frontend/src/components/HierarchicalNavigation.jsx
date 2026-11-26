import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, LayoutDashboard } from 'lucide-react';

/**
 * Breadcrumbs for the survey hierarchy: Overview → Survey → Platform → Respondent → Session.
 * Ids are URL-encoded, since survey ids are often titles with spaces.
 */
const HierarchicalNavigation = ({
  surveyId,
  platformId,
  respondentId,
  sessionId,
  surveyName,
  platformName,
  respondentName,
  sessionName,
}) => {
  const enc = encodeURIComponent;
  const crumbs = [{ label: 'Overview', path: '/', icon: LayoutDashboard }];
  if (surveyId) crumbs.push({ label: surveyName || surveyId, path: `/surveys/${enc(surveyId)}` });
  if (surveyId && platformId) {
    crumbs.push({ label: platformName || platformId, path: `/surveys/${enc(surveyId)}/platforms/${enc(platformId)}` });
  }
  if (surveyId && platformId && respondentId) {
    crumbs.push({
      label: respondentName || respondentId,
      path: `/surveys/${enc(surveyId)}/platforms/${enc(platformId)}/respondents/${enc(respondentId)}`,
    });
  }
  if (surveyId && platformId && respondentId && sessionId) {
    crumbs.push({
      label: sessionName || `Session ${sessionId.substring(0, 8)}`,
      path: `/surveys/${enc(surveyId)}/platforms/${enc(platformId)}/respondents/${enc(respondentId)}/sessions/${enc(sessionId)}`,
    });
  }

  return (
    <nav aria-label="Breadcrumb" className="mb-2">
      <ol className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-gray-500">
        {crumbs.map((crumb, index) => {
          const last = index === crumbs.length - 1;
          const Icon = crumb.icon;
          return (
            <li className="flex min-w-0 items-center gap-1.5" key={crumb.path}>
              {index > 0 && <ChevronRight aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-gray-300" />}
              {last ? (
                <span aria-current="page" className="max-w-[16rem] truncate font-medium text-gray-900">{crumb.label}</span>
              ) : (
                <Link className="flex max-w-[16rem] items-center gap-1 truncate hover:text-blue-700" to={crumb.path}>
                  {Icon && <Icon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />}
                  <span className="truncate">{crumb.label}</span>
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default HierarchicalNavigation;
