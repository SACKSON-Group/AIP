'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { projectsApi, Project, ProjectCreate } from '../../../lib/api';

const SECTORS = ['Energy', 'Mining', 'Water', 'Transport', 'Ports', 'Rail', 'Roads', 'Agriculture', 'Health'];
const STAGES = ['Concept', 'Feasibility', 'Procurement', 'Construction', 'Operation'];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [filter, setFilter] = useState({ sector: '', country: '', stage: '' });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ProjectCreate>();
  const { register: registerEdit, handleSubmit: handleSubmitEdit, reset: resetEdit, setValue: setEditValue, formState: { errors: editErrors } } = useForm<ProjectCreate>();

  const fetchProjects = async () => {
    try {
      const params: Record<string, string> = {};
      if (filter.sector) params.sector = filter.sector;
      if (filter.country) params.country = filter.country;
      if (filter.stage) params.stage = filter.stage;
      const data = await projectsApi.list(params);
      setProjects(data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [filter]);

  const onSubmit = async (data: ProjectCreate) => {
    try {
      await projectsApi.create(data);
      setShowModal(false);
      reset();
      fetchProjects();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    // Set form values
    Object.entries(project).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        setEditValue(key as keyof ProjectCreate, value);
      }
    });
    setShowEditModal(true);
  };

  const onEditSubmit = async (data: ProjectCreate) => {
    if (!editingProject) return;
    try {
      await projectsApi.update(editingProject.id, data);
      setShowEditModal(false);
      setEditingProject(null);
      resetEdit();
      fetchProjects();
    } catch (error) {
      console.error('Failed to update project:', error);
    }
  };

  const handleDeleteProject = async (id: number) => {
    if (!confirm('Are you sure you want to delete this project?')) return;
    try {
      await projectsApi.delete(id);
      fetchProjects();
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  const countries = [...new Set(projects.map(p => p.country))];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          New Project
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={filter.sector}
            onChange={(e) => setFilter({ ...filter, sector: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Sectors</option>
            {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={filter.stage}
            onChange={(e) => setFilter({ ...filter, stage: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Stages</option>
            {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={filter.country}
            onChange={(e) => setFilter({ ...filter, country: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Countries</option>
            {countries.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Projects Table */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Country</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stage</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Est. CAPEX</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Funding Gap</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {projects.length > 0 ? (
                projects.map((project) => (
                  <tr key={project.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{project.name}</div>
                      <div className="text-sm text-gray-500">{project.revenue_model}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                        {project.sector}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">{project.country}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStageColor(project.stage)}`}>
                        {project.stage}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      ${formatNumber(project.estimated_capex)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {project.funding_gap ? `$${formatNumber(project.funding_gap)}` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                      <button
                        onClick={() => setSelectedProject(project)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleEditProject(project)}
                        className="text-green-600 hover:text-green-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No projects found. Create your first project to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Project Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">Create New Project</h2>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                  <XIcon className="w-6 h-6" />
                </button>
              </div>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
                  <input
                    {...register('name', { required: 'Name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sector *</label>
                  <select
                    {...register('sector', { required: 'Sector is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select sector</option>
                    {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  {errors.sector && <p className="text-red-500 text-sm mt-1">{errors.sector.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Country *</label>
                  <input
                    {...register('country', { required: 'Country is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.country && <p className="text-red-500 text-sm mt-1">{errors.country.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                  <input
                    {...register('region')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stage *</label>
                  <select
                    {...register('stage', { required: 'Stage is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select stage</option>
                    {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  {errors.stage && <p className="text-red-500 text-sm mt-1">{errors.stage.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estimated CAPEX ($) *</label>
                  <input
                    {...register('estimated_capex', { required: 'CAPEX is required', valueAsNumber: true })}
                    type="number"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.estimated_capex && <p className="text-red-500 text-sm mt-1">{errors.estimated_capex.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Funding Gap ($)</label>
                  <input
                    {...register('funding_gap', { valueAsNumber: true })}
                    type="number"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Revenue Model *</label>
                  <input
                    {...register('revenue_model', { required: 'Revenue model is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., PPA, Tolling, etc."
                  />
                  {errors.revenue_model && <p className="text-red-500 text-sm mt-1">{errors.revenue_model.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Offtaker</label>
                  <input
                    {...register('offtaker')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Technology</label>
                  <input
                    {...register('technology')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Project Modal */}
      {selectedProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">{selectedProject.name}</h2>
                <button onClick={() => setSelectedProject(null)} className="text-gray-400 hover:text-gray-600">
                  <XIcon className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <DetailItem label="Sector" value={selectedProject.sector} />
                <DetailItem label="Country" value={selectedProject.country} />
                <DetailItem label="Region" value={selectedProject.region || '-'} />
                <DetailItem label="Stage" value={selectedProject.stage} />
                <DetailItem label="Estimated CAPEX" value={`$${formatNumber(selectedProject.estimated_capex)}`} />
                <DetailItem label="Funding Gap" value={selectedProject.funding_gap ? `$${formatNumber(selectedProject.funding_gap)}` : '-'} />
                <DetailItem label="Revenue Model" value={selectedProject.revenue_model} />
                <DetailItem label="Offtaker" value={selectedProject.offtaker || '-'} />
                <DetailItem label="Technology" value={selectedProject.technology || '-'} />
                <DetailItem label="EPC Status" value={selectedProject.epc_status || '-'} />
                <DetailItem label="ESG Category" value={selectedProject.esg_category || '-'} />
                <DetailItem label="Permits Status" value={selectedProject.permits_status || '-'} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium text-gray-900">{value}</p>
    </div>
  );
}

function getStageColor(stage: string) {
  const colors: Record<string, string> = {
    Concept: 'bg-gray-100 text-gray-800',
    Feasibility: 'bg-blue-100 text-blue-800',
    Procurement: 'bg-yellow-100 text-yellow-800',
    Construction: 'bg-orange-100 text-orange-800',
    Operation: 'bg-green-100 text-green-800',
  };
  return colors[stage] || 'bg-gray-100 text-gray-800';
}

function formatNumber(num: number) {
  if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}
