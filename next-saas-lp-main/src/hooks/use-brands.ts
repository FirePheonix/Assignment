"use client";

import { useState, useEffect, useCallback } from 'react';
import { brandsAPI, Brand, CreateBrandData } from '@/lib/api/brands';
import { toast } from 'sonner';

export function useBrands() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [defaultBrand, setDefaultBrand] = useState<Brand | null>(null);

  const fetchBrands = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await brandsAPI.getBrands();
      setBrands(data);
      
      // Find default brand
      const defaultBrandItem = data.find(brand => brand.is_default);
      setDefaultBrand(defaultBrandItem || null);
    } catch (error) {
      console.error('Failed to fetch brands:', error);
      toast.error('Failed to fetch brands');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createBrand = useCallback(async (data: CreateBrandData) => {
    try {
      const newBrand = await brandsAPI.createBrand(data);
      setBrands(prev => [...prev, newBrand]);
      
      // If this is the first brand, it becomes default
      if (brands.length === 0) {
        setDefaultBrand(newBrand);
      }
      
      toast.success('Brand created successfully');
      return newBrand;
    } catch (error: any) {
      console.error('Failed to create brand:', error);
      toast.error(error.message || 'Failed to create brand');
      throw error;
    }
  }, [brands.length]);

  const updateBrand = useCallback(async (brandId: number, data: Partial<CreateBrandData>) => {
    try {
      const updatedBrand = await brandsAPI.updateBrand(brandId, data);
      setBrands(prev => prev.map(brand => brand.id === brandId ? updatedBrand : brand));
      
      // Update default brand if it's the same
      if (defaultBrand?.id === brandId) {
        setDefaultBrand(updatedBrand);
      }
      
      toast.success('Brand updated successfully');
      return updatedBrand;
    } catch (error: any) {
      console.error('Failed to update brand:', error);
      toast.error(error.message || 'Failed to update brand');
      throw error;
    }
  }, [defaultBrand?.id]);

  const setDefault = useCallback(async (brandId: number) => {
    try {
      await brandsAPI.setDefaultBrand(brandId);
      
      // Update local state
      setBrands(prev => prev.map(brand => ({
        ...brand,
        is_default: brand.id === brandId,
      })));
      
      const newDefaultBrand = brands.find(brand => brand.id === brandId);
      setDefaultBrand(newDefaultBrand || null);
      
      toast.success('Default brand updated');
    } catch (error: any) {
      console.error('Failed to set default brand:', error);
      toast.error(error.message || 'Failed to set default brand');
    }
  }, [brands]);

  useEffect(() => {
    fetchBrands();
  }, [fetchBrands]);

  return {
    brands,
    defaultBrand,
    isLoading,
    createBrand,
    updateBrand,
    setDefault,
    refetch: fetchBrands,
  };
}