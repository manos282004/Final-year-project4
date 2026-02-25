import { Store, Wrench, Package } from 'lucide-react';

export const BUSINESS_TYPES = [
  { id: 'showroom', name: 'Two-Wheeler Showroom', icon: Store },
  { id: 'service', name: 'Two-Wheeler Service Centre', icon: Wrench },
  { id: 'spares', name: 'Two-Wheeler Spare Parts Shop', icon: Package },
];

interface BusinessTypeSelectorProps {
  selectedType: string;
  onSelectType: (typeId: string) => void;
}

export default function BusinessTypeSelector({
  selectedType,
  onSelectType,
}: BusinessTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {BUSINESS_TYPES.map((type) => {
        const Icon = type.icon;
        const isSelected = selectedType === type.id;

        return (
          <button
            key={type.id}
            onClick={() => onSelectType(type.id)}
            className={`p-6 rounded-xl border-2 transition-all transform hover:scale-105 ${
              isSelected
                ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-green-50 shadow-lg'
                : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md'
            }`}
          >
            <div className="flex flex-col items-center space-y-3">
              <div
                className={`p-4 rounded-full ${
                  isSelected
                    ? 'bg-gradient-to-br from-blue-500 to-green-500'
                    : 'bg-gray-100'
                }`}
              >
                <Icon
                  className={`w-8 h-8 ${
                    isSelected ? 'text-white' : 'text-gray-600'
                  }`}
                />
              </div>
              <span
                className={`text-center font-semibold ${
                  isSelected
                    ? 'text-blue-600'
                    : 'text-gray-700'
                }`}
              >
                {type.name}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
