# 🔧 Technical Specifications

## 📋 **SYSTEM ARCHITECTURE**

### **Overall Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (Node.js)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ - Student Portal│    │ - REST APIs     │    │ - Normalized    │
│ - Admin Dashboard│   │ - Authentication│    │ - Indexed       │
│ - Responsive UI │    │ - Business Logic│    │ - Materialized  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Technology Stack**

#### **Frontend**
```typescript
// Core Framework
- Nuxt 3 (Full-stack Vue framework)
- Vue 3 + TypeScript
- Tailwind CSS + Vuetify

// State Management & Data Fetching
- Pinia (Global State)
- Nuxt built-in $fetch (Server State)
- VeeValidate + Zod (Form Validation)

// Additional Libraries
- VueUse (Vue utilities)
- Chart.js + vue-chartjs (Charts for Admin)
- jsPDF (Document Generation)
- Nuxt UI (Modern components)
```

#### **Backend**
```typescript
// Core Framework
- Node.js 20+ LTS
- Express.js + TypeScript
- Prisma ORM

// Authentication & Security
- JWT (jsonwebtoken)
- bcrypt (Password Hashing)
- helmet (Security Headers)
- cors (CORS Policy)

// Validation & Utilities
- Zod (Schema Validation)
- multer (File Upload)
- nodemailer (Email Service)
- winston (Logging)
```

#### **Database**
```sql
-- Database System
- PostgreSQL 15+
- Extensions: uuid-ossp, pg_trgm, btree_gist

-- Performance Features
- Materialized Views
- Full-text Search
- Proper Indexing
- Connection Pooling
```

#### **DevOps & Deployment**
```bash
# Development
- Docker + Docker Compose
- ESLint + Prettier
- Husky (Git Hooks)
- Vitest + Vue Test Utils

# Production
- Vercel/Netlify (Nuxt SSR)
- Railway/Render (Backend API)
- Supabase/PlanetScale (Database)
- Cloudinary (File Storage)
```

---

## 🗄️ **DATABASE SPECIFICATIONS**

### **Extended Schema (Phase 1)**

#### **Students Table**
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_code VARCHAR(20) UNIQUE NOT NULL, -- Format: FU2025001
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    address TEXT,
    program_id UUID REFERENCES programs(id),
    campus_id UUID REFERENCES campuses(id),
    admission_year INTEGER DEFAULT 2025,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'graduated', 'suspended', 'transferred')),
    gpa DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_students_student_code ON students(student_code);
CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_program_id ON students(program_id);
CREATE INDEX idx_students_campus_id ON students(campus_id);
CREATE INDEX idx_students_admission_year ON students(admission_year);
```

#### **Applications Table**
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_code VARCHAR(20) UNIQUE NOT NULL, -- Format: APP2025001
    student_name VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    program_id UUID NOT NULL REFERENCES programs(id),
    campus_id UUID NOT NULL REFERENCES campuses(id),
    admission_method_id UUID REFERENCES admission_methods(id),
    scholarship_id UUID REFERENCES scholarships(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'approved', 'rejected', 'cancelled')),
    priority_score INTEGER DEFAULT 0,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_applications_code ON applications(application_code);
CREATE INDEX idx_applications_email ON applications(email);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_program_id ON applications(program_id);
CREATE INDEX idx_applications_campus_id ON applications(campus_id);
CREATE INDEX idx_applications_submitted_at ON applications(submitted_at);
```

#### **Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'admin', 'staff', 'super_admin')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### **Application Documents Table**
```sql
CREATE TABLE application_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('transcript', 'certificate', 'id_card', 'photo', 'other')),
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_app_docs_application_id ON application_documents(application_id);
CREATE INDEX idx_app_docs_type ON application_documents(document_type);
```

### **Business Logic Functions**

#### **Tuition Calculation Function**
```sql
CREATE OR REPLACE FUNCTION calculate_total_tuition(
    p_program_id UUID,
    p_campus_id UUID,
    p_scholarship_percentage DECIMAL DEFAULT 0
) RETURNS TABLE (
    foundation_fee DECIMAL,
    semester_1_3_total DECIMAL,
    semester_4_6_total DECIMAL,
    semester_7_9_total DECIMAL,
    total_program_cost DECIMAL,
    scholarship_discount DECIMAL,
    final_cost DECIMAL
) AS $$
DECLARE
    v_foundation_fee DECIMAL;
    v_sem_1_3_fee DECIMAL;
    v_sem_4_6_fee DECIMAL;
    v_sem_7_9_fee DECIMAL;
    v_total_cost DECIMAL;
    v_scholarship_amount DECIMAL;
BEGIN
    -- Get foundation fee
    SELECT ff.discounted_fee INTO v_foundation_fee
    FROM foundation_fees ff
    WHERE ff.campus_id = p_campus_id AND ff.year = 2025;

    -- Get semester fees
    SELECT pt.semester_group_1_3_fee, pt.semester_group_4_6_fee, pt.semester_group_7_9_fee
    INTO v_sem_1_3_fee, v_sem_4_6_fee, v_sem_7_9_fee
    FROM progressive_tuition pt
    WHERE pt.program_id = p_program_id AND pt.campus_id = p_campus_id AND pt.year = 2025;

    -- Calculate totals
    v_total_cost := v_foundation_fee + (v_sem_1_3_fee * 3) + (v_sem_4_6_fee * 3) + (v_sem_7_9_fee * 3);
    v_scholarship_amount := v_total_cost * (p_scholarship_percentage / 100);

    RETURN QUERY SELECT
        v_foundation_fee,
        v_sem_1_3_fee * 3,
        v_sem_4_6_fee * 3,
        v_sem_7_9_fee * 3,
        v_total_cost,
        v_scholarship_amount,
        v_total_cost - v_scholarship_amount;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔌 **API SPECIFICATIONS**

### **Authentication Endpoints**

#### **POST /api/auth/register**
```typescript
// Request Body
interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role?: 'student' | 'admin' | 'staff';
}

// Response
interface RegisterResponse {
  success: boolean;
  message: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
  };
  token: string;
}
```

#### **POST /api/auth/login**
```typescript
// Request Body
interface LoginRequest {
  email: string;
  password: string;
}

// Response
interface LoginResponse {
  success: boolean;
  message: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
    lastLogin: string;
  };
  token: string;
}
```

### **Application Endpoints**

#### **POST /api/applications**
```typescript
// Request Body
interface CreateApplicationRequest {
  studentName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  address: string;
  programId: string;
  campusId: string;
  admissionMethodId: string;
  scholarshipId?: string;
}

// Response
interface CreateApplicationResponse {
  success: boolean;
  message: string;
  application: {
    id: string;
    applicationCode: string;
    status: string;
    submittedAt: string;
  };
}
```

#### **GET /api/applications**
```typescript
// Query Parameters
interface GetApplicationsQuery {
  page?: number;
  limit?: number;
  status?: string;
  programId?: string;
  campusId?: string;
  sortBy?: 'submittedAt' | 'status' | 'priorityScore';
  sortOrder?: 'asc' | 'desc';
}

// Response
interface GetApplicationsResponse {
  success: boolean;
  data: {
    applications: Application[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
    };
  };
}
```

### **Tuition Calculation Endpoints**

#### **POST /api/tuition/calculate**
```typescript
// Request Body
interface CalculateTuitionRequest {
  programId: string;
  campusId: string;
  scholarshipId?: string;
}

// Response
interface CalculateTuitionResponse {
  success: boolean;
  data: {
    foundationFee: number;
    semesterFees: {
      group1_3: number;
      group4_6: number;
      group7_9: number;
    };
    totalProgramCost: number;
    scholarshipDiscount: number;
    finalCost: number;
    breakdown: {
      foundationFee: number;
      semester1_3Total: number;
      semester4_6Total: number;
      semester7_9Total: number;
    };
  };
}
```

---

## 🎨 **FRONTEND SPECIFICATIONS**

### **Nuxt 3 Project Structure**
```bash
frontend/
├── nuxt.config.ts              # Nuxt configuration
├── app.vue                     # Root component
├── layouts/
│   ├── default.vue            # Default layout
│   └── dashboard.vue          # Dashboard layout
├── pages/
│   ├── index.vue              # Landing page
│   ├── programs/
│   │   ├── index.vue          # Program catalog
│   │   └── [id].vue           # Program details
│   └── dashboard/
│       ├── index.vue          # Student dashboard
│       └── applications/
├── components/
│   ├── forms/                 # Form components
│   ├── ui/                    # UI components
│   └── charts/                # Chart components
├── composables/               # Vue composables
├── stores/                    # Pinia stores
├── server/                    # Nuxt server API
└── types/                     # TypeScript types
```

### **Nuxt 3 Configuration**
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Development configuration
  devtools: { enabled: true },

  // TypeScript configuration
  typescript: {
    strict: true,
    typeCheck: true
  },

  // CSS framework
  css: [
    'vuetify/lib/styles/main.sass',
    '@/assets/css/main.css'
  ],

  // Modules
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxtjs/color-mode',
    '@vee-validate/nuxt'
  ],

  // Build configuration
  build: {
    transpile: ['vuetify']
  },

  // Runtime config
  runtimeConfig: {
    // Private keys (only available on server-side)
    jwtSecret: process.env.JWT_SECRET,
    databaseUrl: process.env.DATABASE_URL,

    // Public keys (exposed to client-side)
    public: {
      apiBase: process.env.API_BASE_URL || 'http://localhost:3001',
      appName: 'FPT University 2025'
    }
  },

  // App configuration
  app: {
    head: {
      title: 'FPT University 2025 - Hệ thống tuyển sinh',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Hệ thống tuyển sinh trực tuyến FPT University 2025' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  },

  // Server-side rendering
  ssr: true,

  // Route rules for optimization
  routeRules: {
    // Homepage pre-rendered at build time
    '/': { prerender: true },
    // Programs page pre-rendered at build time
    '/programs': { prerender: true },
    // Dashboard pages require authentication
    '/dashboard/**': { ssr: false },
    // Admin pages require authentication
    '/admin/**': { ssr: false }
  },

  // Vite configuration
  vite: {
    define: {
      'process.env.DEBUG': false,
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@use "@/assets/scss/variables.scss" as *;'
        }
      }
    }
  }
});
```

### **Component Architecture**

#### **Layout Components**
```vue
<!-- layouts/default.vue -->
<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    <main class="container mx-auto px-4 py-8">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>

<!-- layouts/dashboard.vue -->
<template>
  <div class="min-h-screen bg-gray-50">
    <DashboardHeader :user="user" />
    <div class="flex">
      <DashboardSidebar :navigation="navigation" />
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
interface Props {
  user: User;
  navigation: NavigationItem[];
}
defineProps<Props>()
</script>
```

#### **Form Components**
```vue
<!-- components/forms/ApplicationForm.vue -->
<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <div class="grid md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium mb-2">Họ và tên</label>
        <input
          v-model="form.studentName"
          :class="{ 'border-red-500': errors.studentName }"
          class="w-full px-3 py-2 border rounded-lg"
          placeholder="Nhập họ và tên"
        />
        <span v-if="errors.studentName" class="text-red-500 text-sm">
          {{ errors.studentName }}
        </span>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">Email</label>
        <input
          v-model="form.email"
          type="email"
          :class="{ 'border-red-500': errors.email }"
          class="w-full px-3 py-2 border rounded-lg"
          placeholder="example@email.com"
        />
        <span v-if="errors.email" class="text-red-500 text-sm">
          {{ errors.email }}
        </span>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium mb-2">Chương trình học</label>
      <select
        v-model="form.programId"
        :class="{ 'border-red-500': errors.programId }"
        class="w-full px-3 py-2 border rounded-lg"
      >
        <option value="">Chọn chương trình</option>
        <option v-for="program in programs" :key="program.id" :value="program.id">
          {{ program.name }}
        </option>
      </select>
    </div>

    <button
      type="submit"
      :disabled="isLoading"
      class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
    >
      <span v-if="isLoading">Đang xử lý...</span>
      <span v-else>Nộp đơn ứng tuyển</span>
    </button>
  </form>
</template>

<script setup lang="ts">
interface Props {
  programs: Program[];
  initialData?: Partial<ApplicationFormData>;
  isLoading?: boolean;
}

interface Emits {
  submit: [data: ApplicationFormData];
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Form state with VeeValidate
const { handleSubmit, errors } = useForm({
  validationSchema: applicationSchema
});

const form = reactive({
  studentName: props.initialData?.studentName || '',
  email: props.initialData?.email || '',
  programId: props.initialData?.programId || '',
  // ... other fields
});

const handleSubmit = handleSubmit((values) => {
  emit('submit', values as ApplicationFormData);
});
</script>
```

```vue
<!-- components/forms/TuitionCalculator.vue -->
<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h3 class="text-xl font-semibold mb-4">Tính học phí</h3>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-2">Chương trình học</label>
        <select v-model="selectedProgram" class="w-full px-3 py-2 border rounded-lg">
          <option value="">Chọn chương trình</option>
          <option v-for="program in programs" :key="program.id" :value="program">
            {{ program.name }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">Cơ sở</label>
        <select v-model="selectedCampus" class="w-full px-3 py-2 border rounded-lg">
          <option value="">Chọn cơ sở</option>
          <option v-for="campus in campuses" :key="campus.id" :value="campus">
            {{ campus.name }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">Học bổng</label>
        <select v-model="selectedScholarship" class="w-full px-3 py-2 border rounded-lg">
          <option value="">Không có học bổng</option>
          <option v-for="scholarship in scholarships" :key="scholarship.id" :value="scholarship">
            {{ scholarship.name }} ({{ scholarship.percentage }}%)
          </option>
        </select>
      </div>

      <button
        @click="calculateTuition"
        :disabled="!canCalculate"
        class="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
      >
        Tính học phí
      </button>
    </div>

    <!-- Results -->
    <div v-if="result" class="mt-6 p-4 bg-gray-50 rounded-lg">
      <h4 class="font-semibold mb-2">Kết quả tính toán:</h4>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span>Học phí định hướng:</span>
          <span class="font-medium">{{ formatCurrency(result.foundationFee) }}</span>
        </div>
        <div class="flex justify-between">
          <span>Tổng học phí chương trình:</span>
          <span class="font-medium">{{ formatCurrency(result.totalProgramCost) }}</span>
        </div>
        <div v-if="result.scholarshipDiscount > 0" class="flex justify-between text-green-600">
          <span>Giảm học bổng:</span>
          <span class="font-medium">-{{ formatCurrency(result.scholarshipDiscount) }}</span>
        </div>
        <hr class="my-2">
        <div class="flex justify-between text-lg font-bold">
          <span>Tổng cần thanh toán:</span>
          <span>{{ formatCurrency(result.finalCost) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  programs: Program[];
  campuses: Campus[];
  scholarships: Scholarship[];
}

interface Emits {
  calculate: [result: TuitionCalculation];
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const selectedProgram = ref<Program | null>(null);
const selectedCampus = ref<Campus | null>(null);
const selectedScholarship = ref<Scholarship | null>(null);
const result = ref<TuitionCalculation | null>(null);

const canCalculate = computed(() =>
  selectedProgram.value && selectedCampus.value
);

const calculateTuition = async () => {
  if (!canCalculate.value) return;

  const { data } = await $fetch('/api/tuition/calculate', {
    method: 'POST',
    body: {
      programId: selectedProgram.value!.id,
      campusId: selectedCampus.value!.id,
      scholarshipId: selectedScholarship.value?.id
    }
  });

  result.value = data;
  emit('calculate', data);
};

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(amount);
};
</script>
```

#### **Data Display Components**
```vue
<!-- components/tables/ApplicationsTable.vue -->
<template>
  <div class="bg-white rounded-lg shadow overflow-hidden">
    <div class="px-6 py-4 border-b">
      <h3 class="text-lg font-semibold">Danh sách đơn ứng tuyển</h3>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Mã đơn
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Họ tên
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Chương trình
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Trạng thái
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Ngày nộp
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Thao tác
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="application in applications" :key="application.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              {{ application.applicationCode }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              {{ application.studentName }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
              {{ application.program?.name }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="getStatusClass(application.status)" class="px-2 py-1 text-xs rounded-full">
                {{ getStatusText(application.status) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(application.submittedAt) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm space-x-2">
              <button
                @click="$emit('view', application)"
                class="text-blue-600 hover:text-blue-800"
              >
                Xem
              </button>
              <select
                :value="application.status"
                @change="$emit('statusChange', application.id, $event.target.value)"
                class="text-sm border rounded px-2 py-1"
              >
                <option value="pending">Chờ xử lý</option>
                <option value="reviewing">Đang xem xét</option>
                <option value="approved">Đã duyệt</option>
                <option value="rejected">Từ chối</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="isLoading" class="p-6 text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  applications: Application[];
  isLoading?: boolean;
}

interface Emits {
  statusChange: [id: string, status: string];
  view: [application: Application];
}

defineProps<Props>();
defineEmits<Emits>();

const getStatusClass = (status: string) => {
  const classes = {
    pending: 'bg-yellow-100 text-yellow-800',
    reviewing: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800'
  };
  return classes[status] || 'bg-gray-100 text-gray-800';
};

const getStatusText = (status: string) => {
  const texts = {
    pending: 'Chờ xử lý',
    reviewing: 'Đang xem xét',
    approved: 'Đã duyệt',
    rejected: 'Từ chối'
  };
  return texts[status] || status;
};

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('vi-VN');
};
</script>
```

```vue
<!-- components/cards/ProgramCard.vue -->
<template>
  <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer" @click="$emit('select')">
    <div class="p-6">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-1">
            {{ program.name }}
          </h3>
          <p class="text-sm text-gray-600">
            {{ program.nameEn }}
          </p>
        </div>
        <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
          {{ program.code }}
        </span>
      </div>

      <div class="space-y-2 mb-4">
        <div class="flex items-center text-sm text-gray-600">
          <Icon name="academic-cap" class="w-4 h-4 mr-2" />
          <span>{{ program.department?.name }}</span>
        </div>

        <div class="flex items-center text-sm text-gray-600">
          <Icon name="clock" class="w-4 h-4 mr-2" />
          <span>{{ program.durationYears }} năm</span>
        </div>

        <div v-if="campus" class="flex items-center text-sm text-gray-600">
          <Icon name="map-pin" class="w-4 h-4 mr-2" />
          <span>{{ campus.name }}</span>
        </div>
      </div>

      <div v-if="tuitionRange" class="border-t pt-4">
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-600">Học phí:</span>
          <div class="text-right">
            <div class="text-sm font-medium text-gray-900">
              {{ formatCurrency(tuitionRange.min) }} - {{ formatCurrency(tuitionRange.max) }}
            </div>
            <div class="text-xs text-gray-500">
              /học kỳ
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4 pt-4 border-t">
        <button class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
          Xem chi tiết
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  program: Program;
  campus?: Campus;
  tuitionRange?: {
    min: number;
    max: number;
  };
}

interface Emits {
  select: [];
}

defineProps<Props>();
defineEmits<Emits>();

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(amount);
};
</script>
```

### **State Management**

#### **Pinia Stores**
```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  const login = async (credentials: LoginCredentials) => {
    const { data } = await $fetch('/api/auth/login', {
      method: 'POST',
      body: credentials
    });

    user.value = data.user;
    token.value = data.token;

    // Store in localStorage
    localStorage.setItem('auth_token', data.token);

    // Set default header for future requests
    $fetch.defaults.headers.Authorization = `Bearer ${data.token}`;
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
    delete $fetch.defaults.headers.Authorization;

    // Redirect to login
    navigateTo('/login');
  };

  const updateProfile = async (data: Partial<User>) => {
    const { data: updatedUser } = await $fetch('/api/auth/profile', {
      method: 'PUT',
      body: data
    });

    user.value = updatedUser;
  };

  // Initialize from localStorage
  const initAuth = () => {
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      token.value = savedToken;
      $fetch.defaults.headers.Authorization = `Bearer ${savedToken}`;
      // Fetch user profile
      fetchProfile();
    }
  };

  const fetchProfile = async () => {
    try {
      const { data } = await $fetch('/api/auth/profile');
      user.value = data;
    } catch (error) {
      logout();
    }
  };

  return {
    user: readonly(user),
    token: readonly(token),
    isAuthenticated,
    login,
    logout,
    updateProfile,
    initAuth
  };
});

// stores/applications.ts
export const useApplicationStore = defineStore('applications', () => {
  const applications = ref<Application[]>([]);
  const currentApplication = ref<Application | null>(null);
  const isLoading = ref(false);

  const fetchApplications = async (filters?: ApplicationFilters) => {
    isLoading.value = true;
    try {
      const { data } = await $fetch('/api/applications', {
        query: filters
      });
      applications.value = data.applications;
    } finally {
      isLoading.value = false;
    }
  };

  const createApplication = async (data: CreateApplicationData) => {
    isLoading.value = true;
    try {
      const { data: newApplication } = await $fetch('/api/applications', {
        method: 'POST',
        body: data
      });

      applications.value.unshift(newApplication);
      return newApplication;
    } finally {
      isLoading.value = false;
    }
  };

  const updateApplication = async (id: string, data: Partial<Application>) => {
    const { data: updatedApplication } = await $fetch(`/api/applications/${id}`, {
      method: 'PUT',
      body: data
    });

    const index = applications.value.findIndex(app => app.id === id);
    if (index !== -1) {
      applications.value[index] = updatedApplication;
    }

    return updatedApplication;
  };

  const getApplicationById = (id: string) => {
    return applications.value.find(app => app.id === id);
  };

  return {
    applications: readonly(applications),
    currentApplication: readonly(currentApplication),
    isLoading: readonly(isLoading),
    fetchApplications,
    createApplication,
    updateApplication,
    getApplicationById
  };
});

// stores/programs.ts
export const useProgramStore = defineStore('programs', () => {
  const programs = ref<Program[]>([]);
  const departments = ref<Department[]>([]);
  const campuses = ref<Campus[]>([]);

  const fetchPrograms = async () => {
    const { data } = await $fetch('/api/programs');
    programs.value = data;
  };

  const fetchDepartments = async () => {
    const { data } = await $fetch('/api/departments');
    departments.value = data;
  };

  const fetchCampuses = async () => {
    const { data } = await $fetch('/api/campuses');
    campuses.value = data;
  };

  const searchPrograms = async (query: string) => {
    const { data } = await $fetch('/api/programs/search', {
      query: { q: query }
    });
    return data;
  };

  const getProgramById = (id: string) => {
    return programs.value.find(program => program.id === id);
  };

  return {
    programs: readonly(programs),
    departments: readonly(departments),
    campuses: readonly(campuses),
    fetchPrograms,
    fetchDepartments,
    fetchCampuses,
    searchPrograms,
    getProgramById
  };
});
```

### **Responsive Design Breakpoints**
```css
/* Tailwind CSS Breakpoints */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large desktop */
```

---

## 🔒 **SECURITY SPECIFICATIONS**

### **Authentication & Authorization**
```typescript
// JWT Token Structure
interface JWTPayload {
  userId: string;
  email: string;
  role: string;
  iat: number;
  exp: number;
}

// Role-based Access Control
const PERMISSIONS = {
  student: ['read:own_profile', 'create:application', 'read:own_applications'],
  staff: ['read:applications', 'update:application_status'],
  admin: ['read:all', 'create:all', 'update:all', 'delete:all'],
  super_admin: ['*']
};
```

### **Input Validation**
```typescript
// Zod Schemas
const ApplicationSchema = z.object({
  studentName: z.string().min(2).max(255),
  email: z.string().email(),
  phone: z.string().regex(/^[0-9+\-\s()]+$/),
  dateOfBirth: z.string().datetime(),
  programId: z.string().uuid(),
  campusId: z.string().uuid(),
});
```

### **Security Headers**
```typescript
// Helmet Configuration
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
```

---

## 📊 **PERFORMANCE SPECIFICATIONS**

### **Database Optimization**
```sql
-- Query Performance Targets
- Simple queries: < 10ms
- Complex joins: < 100ms
- Search queries: < 200ms
- Report generation: < 2s

-- Connection Pool Settings
- Min connections: 5
- Max connections: 20
- Idle timeout: 30s
- Connection timeout: 5s
```

### **Frontend Performance**
```typescript
// Performance Targets
- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- First Input Delay: < 100ms

// Optimization Strategies
- Code splitting by route
- Image optimization with Next.js
- Lazy loading for non-critical components
- Service worker for caching
```

### **API Performance**
```typescript
// Response Time Targets
- Authentication: < 200ms
- CRUD operations: < 300ms
- Search endpoints: < 500ms
- Report generation: < 2s

// Optimization Strategies
- Redis caching for frequent queries
- Database query optimization
- Response compression
- Rate limiting
```

---

## 🚀 **DEPLOYMENT SPECIFICATIONS**

### **Environment Configuration**
```bash
# Development
NODE_ENV=development
DATABASE_URL=postgresql://localhost:5432/fpt_university_dev
JWT_SECRET=dev_secret_key
REDIS_URL=redis://localhost:6379

# Production
NODE_ENV=production
DATABASE_URL=postgresql://prod_host:5432/fpt_university_prod
JWT_SECRET=secure_production_secret
REDIS_URL=redis://prod_redis:6379
```

### **Docker Configuration**
```dockerfile
# Dockerfile for Backend
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### **CI/CD Pipeline**
```yaml
# GitHub Actions
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
```

**Ready for implementation! 🚀**
