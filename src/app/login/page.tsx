'use client';

import { useForm } from 'react-hook-form';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';

interface LoginForm {
  username: string;
  password: string;
}

export default function Login() {
  const { register, handleSubmit } = useForm<LoginForm>();
 const login = async (username: string, password: string) => {
    const res = await axios.post('http://127.0.0.1:8000/login', { username, password });
  const router = useRouter();

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data.username, data.password);
      router.push('/projects');
    } catch (error) {
      alert('Login failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <form onSubmit={handleSubmit(onSubmit)} className="p-6 bg-white rounded shadow-md">
        <input {...register('username')} placeholder="Username" className="mb-4 p-2 border w-full" />
        <input {...register('password')} type="password" placeholder="Password" className="mb-4 p-2 border w-full" />
        <button type="submit" className="bg-blue-500 text-white p-2 w-full">Login</button>
      </form>
    </div>
  );
};