export interface Hospital {
  id: number;
  code: string;
  name: string;
  address: string;
}

export interface CreateHospitalRequest {
  code: string;
  name: string;
  address: string;
}

export interface UpdateHospitalRequest {
  code: string;
  name: string;
  address: string;
}